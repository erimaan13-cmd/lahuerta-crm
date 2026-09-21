"""Servicios de aplicación del CRM: leads, cuentas, oportunidades, cotizaciones, actividades, tareas y casos.

Todas las mutaciones registran AuditEvent (RF-21). Las rutas HTTP solo llaman a estas funciones.
"""
from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import config
from app.audit import record, snapshot
from app.models import (Account, Activity, Case, Contact, IntegrationEvent, Lead, Opportunity,
                        Product, ProductInterest, Quote, QuoteItem, Sector, Task, utcnow)
from app.services import pipeline
from app.services.business_time import add_business_hours
from app.services.common import (DomainError, email_domain, get_or_404, norm_email, norm_phone,
                                 norm_text)

LEAD_SOURCES = {"web_contacto", "web_catalogo", "whatsapp", "telefono", "email", "google_ads",
                "meta_ads", "linkedin", "referido", "otro"}
VOLUME_BANDS = {"menor_500kg", "500kg_1t", "mas_1t", "desconocido"}
LEAD_TRANSITIONS = {
    "nuevo": {"contactado", "calificado", "descartado"},
    "contactado": {"calificado", "descartado"},
    "calificado": {"descartado"},  # "convertido" solo vía convert_lead
    "descartado": {"nuevo"},        # reabrir
    "convertido": set(),
}
PACKAGING = {"saco_pp_pead", "saco_kraft_pe", "caja_corrugado"}
CASE_TYPES = {"reclamacion_calidad", "documentacion", "entrega", "facturacion", "otro"}
CASE_SEVERITIES = {"baja", "media", "alta", "critica"}
CASE_TRANSITIONS = {
    "abierto": {"en_proceso", "escalado_qms", "resuelto"},
    "en_proceso": {"escalado_qms", "resuelto"},
    "escalado_qms": {"en_proceso", "resuelto"},
    "resuelto": {"cerrado", "en_proceso"},
    "cerrado": set(),
}
ACTIVITY_TYPES = {"llamada", "correo", "whatsapp", "reunion", "nota", "sistema"}
RELATED_MODELS = {"lead": Lead, "account": Account, "contact": Contact, "opportunity": Opportunity,
                  "case": Case}


# ---------------------------------------------------------------- utilidades
def _band_from_kg(kg: float | None) -> str:
    if kg is None:
        return "desconocido"
    if kg < config.MIN_ORDER_KG:
        return "menor_500kg"
    return "500kg_1t" if kg <= 1000 else "mas_1t"


def _clean(v):
    return v.strip() if isinstance(v, str) and v.strip() else (None if isinstance(v, str) else v)


def _system_activity(db, related_type, related_id, subject, actor_id=None, body=None):
    db.add(Activity(type="sistema", subject=subject, body=body, related_type=related_type,
                    related_id=related_id, actor_id=actor_id))


def match_products(db: Session, text: str | None) -> list[Product]:
    t = norm_text(text)
    if not t:
        return []
    found = []
    for p in db.scalars(select(Product).where(Product.is_active.is_(True))):
        terms = [norm_text(p.name)] + [norm_text(k) for k in (p.keywords or "").split(",") if k.strip()]
        if any(term and term in t for term in terms):
            found.append(p)
    return found


# ---------------------------------------------------------------- leads
def create_lead(db: Session, data: dict, actor_id: str | None = None) -> tuple[Lead, bool]:
    """Crea un lead con deduplicación básica (D-13). Devuelve (lead, creado)."""
    full_name = _clean(data.get("full_name"))
    email = norm_email(_clean(data.get("email")))
    phone = norm_phone(_clean(data.get("phone")))
    if not full_name:
        raise DomainError("El nombre es obligatorio")
    if not (email or phone):
        raise DomainError("Se requiere correo o teléfono")
    source = data.get("source") or "otro"
    if source not in LEAD_SOURCES:
        raise DomainError(f"Origen inválido: {source}")
    sector = _clean(data.get("sector_code"))
    if sector and db.get(Sector, sector) is None:
        raise DomainError(f"Sector desconocido: {sector}")
    kg = data.get("est_volume_kg")
    kg = float(kg) if kg not in (None, "") else None
    if kg is not None and kg <= 0:
        raise DomainError("El volumen estimado debe ser mayor que cero")
    band = data.get("volume_band") or _band_from_kg(kg)
    if band not in VOLUME_BANDS:
        raise DomainError(f"Rango de volumen inválido: {band}")

    # 1) duplicado exacto por correo → no se crea, se registra la interacción
    if email:
        existing = db.scalar(select(Lead).where(Lead.email == email))
        if existing:
            db.add(Activity(type="nota", subject="Nuevo contacto del mismo prospecto (deduplicado)",
                            body=_clean(data.get("message")), related_type="lead",
                            related_id=existing.id, actor_id=actor_id))
            record(db, actor_id, "lead.dedup_merge_activity", "lead", existing.id,
                   after={"source": source})
            db.commit()
            return existing, False

    lead = Lead(full_name=full_name, company_name=_clean(data.get("company_name")), email=email,
                phone=phone, city=_clean(data.get("city")), state=_clean(data.get("state")),
                sector_code=sector, product_interest_text=_clean(data.get("product_interest_text")),
                volume_band=band, est_volume_kg=kg, message=_clean(data.get("message")),
                source=source, campaign=_clean(data.get("campaign")),
                consent_source=_clean(data.get("consent_source")) or f"formulario:{source}",
                owner_id=data.get("owner_id"), is_demo=bool(data.get("is_demo", False)))
    lead.below_minimum = band == "menor_500kg"

    # 2) posibles duplicados (no fusiona)
    dup_conds = []
    if phone:
        dup_conds.append(Lead.phone == phone)
    dom = email_domain(email)
    if dom:
        dup_conds.append(Lead.email.like(f"%@{dom}"))
    if dup_conds:
        other = db.scalar(select(Lead).where(or_(*dup_conds)).order_by(Lead.created_at))
        if other:
            lead.possible_duplicate_of_id = other.id
            lead.duplicate_reason = "mismo teléfono" if phone and other.phone == phone else "mismo dominio"
    if email:
        c = db.scalar(select(Contact).where(Contact.email == email))
        if c:
            lead.duplicate_reason = f"correo de contacto existente (cuenta {c.account_id})"
    if dom and not lead.duplicate_reason:
        acc = db.scalar(select(Account).where(Account.domain == dom))
        if acc:
            lead.duplicate_reason = f"dominio de cuenta existente ({acc.name})"

    db.add(lead)
    db.flush()
    # 3) automatización: tarea de primer contacto (E14 "te contactaremos enseguida")
    db.add(Task(title=f"Primer contacto: {lead.full_name} ({lead.company_name or 's/empresa'})",
                due_at=add_business_hours(utcnow(), config.FIRST_CONTACT_SLA_HOURS),
                priority="alta" if not lead.below_minimum else "baja",
                assignee_id=lead.owner_id, assignee_role="ventas", related_type="lead",
                related_id=lead.id, origin="auto_lead"))
    record(db, actor_id, "lead.create", "lead", lead.id, after=snapshot(lead))
    db.commit()
    return lead, True


def change_lead_status(db: Session, lead_id: str, new_status: str, actor_id: str | None,
                       reason: str | None = None) -> Lead:
    lead = get_or_404(db, Lead, lead_id, "Lead")
    if new_status not in LEAD_TRANSITIONS.get(lead.status, set()):
        raise DomainError(f"Transición de lead no permitida: {lead.status} → {new_status}")
    if new_status == "descartado" and not _clean(reason):
        raise DomainError("Para descartar un lead indica el motivo")
    if new_status == "calificado" and not lead.company_name:
        raise DomainError("Para calificar se requiere el nombre de la empresa")
    before = snapshot(lead)
    lead.status = new_status
    lead.discard_reason = _clean(reason) if new_status == "descartado" else None
    _system_activity(db, "lead", lead.id, f"Estado: {before['status']} → {new_status}", actor_id, reason)
    record(db, actor_id, "lead.status", "lead", lead.id, before, snapshot(lead))
    db.commit()
    return lead


def convert_lead(db: Session, lead_id: str, actor_id: str | None, create_opportunity: bool = True,
                 opp_type: str = "estandar", opp_title: str | None = None) -> dict:
    lead = get_or_404(db, Lead, lead_id, "Lead")
    if lead.status != "calificado":
        raise DomainError("Solo se convierten leads calificados")
    if opp_type not in pipeline.OPP_TYPES:
        raise DomainError(f"Tipo de oportunidad inválido: {opp_type}")
    dom = email_domain(lead.email)
    account = None
    if dom:
        account = db.scalar(select(Account).where(Account.domain == dom))
    if account is None and lead.company_name:
        account = db.scalar(select(Account).where(func.lower(Account.name) == lead.company_name.lower()))
    account_created = account is None
    if account_created:
        account = Account(name=lead.company_name or lead.full_name, domain=dom,
                          sector_code=lead.sector_code, city=lead.city, state=lead.state,
                          owner_id=lead.owner_id or actor_id, is_demo=lead.is_demo)
        db.add(account)
        db.flush()
        record(db, actor_id, "account.create", "account", account.id, after=snapshot(account))

    contact = db.scalar(select(Contact).where(Contact.email == lead.email)) if lead.email else None
    if contact is None:
        contact = Contact(account_id=account.id, full_name=lead.full_name, email=lead.email,
                          phone=lead.phone, is_primary=account_created)
        db.add(contact)
        db.flush()
        record(db, actor_id, "contact.create", "contact", contact.id, after=snapshot(contact))

    opp = None
    if create_opportunity:
        opp = Opportunity(account_id=account.id, contact_id=contact.id, type=opp_type,
                          title=opp_title or f"{lead.product_interest_text or 'Requerimiento'} — {account.name}",
                          est_volume_kg=lead.est_volume_kg, owner_id=lead.owner_id or actor_id,
                          is_demo=lead.is_demo)
        db.add(opp)
        db.flush()
        for p in match_products(db, f"{lead.product_interest_text or ''} {lead.message or ''}"):
            db.add(ProductInterest(opportunity_id=opp.id, product_id=p.id))
        record(db, actor_id, "opportunity.create", "opportunity", opp.id, after=snapshot(opp))

    before = snapshot(lead)
    lead.status = "convertido"
    lead.converted_account_id, lead.converted_contact_id = account.id, contact.id
    lead.converted_opportunity_id = opp.id if opp else None
    _system_activity(db, "account", account.id, f"Lead convertido: {lead.full_name}", actor_id)
    record(db, actor_id, "lead.convert", "lead", lead.id, before, snapshot(lead))
    db.commit()
    return {"lead": lead, "account": account, "contact": contact, "opportunity": opp,
            "account_created": account_created}


# ---------------------------------------------------------------- cuentas / contactos
def create_account(db: Session, data: dict, actor_id: str | None) -> Account:
    name = _clean(data.get("name"))
    if not name:
        raise DomainError("El nombre de la cuenta es obligatorio")
    dom = _clean(data.get("domain"))
    if dom and db.scalar(select(Account).where(Account.domain == dom.lower())):
        raise DomainError(f"Ya existe una cuenta con el dominio {dom}")
    acc = Account(name=name, domain=dom.lower() if dom else None, sector_code=_clean(data.get("sector_code")),
                  city=_clean(data.get("city")), state=_clean(data.get("state")),
                  is_key_account=bool(data.get("is_key_account")), owner_id=data.get("owner_id") or actor_id,
                  is_demo=bool(data.get("is_demo", False)))
    db.add(acc)
    db.flush()
    record(db, actor_id, "account.create", "account", acc.id, after=snapshot(acc))
    db.commit()
    return acc


def create_contact(db: Session, account_id: str, data: dict, actor_id: str | None) -> Contact:
    get_or_404(db, Account, account_id, "Cuenta")
    email = norm_email(_clean(data.get("email")))
    if email and db.scalar(select(Contact).where(Contact.email == email)):
        raise DomainError(f"Ya existe un contacto con el correo {email}")
    c = Contact(account_id=account_id, full_name=_clean(data.get("full_name")) or "", email=email,
                phone=norm_phone(_clean(data.get("phone"))), job_title=_clean(data.get("job_title")),
                is_primary=bool(data.get("is_primary")))
    if not c.full_name:
        raise DomainError("El nombre del contacto es obligatorio")
    db.add(c)
    db.flush()
    record(db, actor_id, "contact.create", "contact", c.id, after=snapshot(c))
    db.commit()
    return c


# ---------------------------------------------------------------- oportunidades
def create_opportunity(db: Session, data: dict, actor_id: str | None) -> Opportunity:
    acc = get_or_404(db, Account, data.get("account_id") or "", "Cuenta")
    opp_type = data.get("type") or "estandar"
    if opp_type not in pipeline.OPP_TYPES:
        raise DomainError(f"Tipo de oportunidad inválido: {opp_type}")
    title = _clean(data.get("title"))
    if not title:
        raise DomainError("El título es obligatorio")
    kg = data.get("est_volume_kg")
    opp = Opportunity(account_id=acc.id, contact_id=data.get("contact_id"), title=title, type=opp_type,
                      est_volume_kg=float(kg) if kg not in (None, "") else None,
                      est_value_mxn=float(data["est_value_mxn"]) if data.get("est_value_mxn") else None,
                      owner_id=data.get("owner_id") or actor_id, is_demo=bool(data.get("is_demo", False)))
    db.add(opp)
    db.flush()
    for pid in data.get("product_ids") or []:
        get_or_404(db, Product, pid, "Producto")
        db.add(ProductInterest(opportunity_id=opp.id, product_id=pid))
    record(db, actor_id, "opportunity.create", "opportunity", opp.id, after=snapshot(opp))
    db.commit()
    return opp


def change_stage(db: Session, opp_id: str, new_stage: str, actor_id: str | None,
                 lost_reason: str | None = None) -> Opportunity:
    opp = get_or_404(db, Opportunity, opp_id, "Oportunidad")
    if opp.stage in pipeline.CLOSED_STAGES:
        raise DomainError("La oportunidad ya está cerrada")
    allowed = pipeline.allowed_next(opp.type, opp.stage)
    if new_stage not in allowed:
        raise DomainError(f"Transición no permitida para '{opp.type}': {opp.stage} → {new_stage}. "
                          f"Permitidas: {', '.join(sorted(allowed)) or 'ninguna'}")
    if new_stage == "cotizacion" and not opp.quotes:
        raise DomainError("Para pasar a Cotización debe existir al menos una cotización")
    if new_stage == "perdida" and not _clean(lost_reason):
        raise DomainError("El motivo de pérdida es obligatorio")
    if new_stage == "ganada" and not opp.quotes:
        raise DomainError("No se puede ganar una oportunidad sin cotización")
    before = snapshot(opp)
    opp.stage = new_stage
    if new_stage in pipeline.CLOSED_STAGES:
        opp.closed_at = utcnow()
        opp.lost_reason = _clean(lost_reason) if new_stage == "perdida" else None
    if new_stage == "ganada":
        for q in opp.quotes:
            if q.status in ("borrador", "enviada"):
                q.status = "aceptada"
                break
        acc = opp.account
        if acc.lifecycle == "prospecto":
            acc.lifecycle = "cliente_activo"
        # Handoff a Administración/ERP mediante outbox (integración futura, D-09)
        db.add(IntegrationEvent(direction="out", system="erp", event_type="opportunity.won",
                                payload={"opportunity_id": opp.id, "account_id": acc.id,
                                         "account_name": acc.name, "erp_customer_ref": acc.erp_customer_ref}))
        db.add(Task(title=f"Alta/pedido en ERP: {acc.name}", assignee_role="administracion",
                    related_type="opportunity", related_id=opp.id, origin="auto_pipeline",
                    due_at=add_business_hours(utcnow(), 9), priority="alta"))
    if new_stage == "desarrollo_formula":
        db.add(Task(title=f"Desarrollar propuesta de fórmula: {opp.title}", assignee_role="calidad",
                    related_type="opportunity", related_id=opp.id, origin="auto_pipeline",
                    due_at=add_business_hours(utcnow(), config.FORMULA_TASK_HOURS)))
    _system_activity(db, "opportunity", opp.id,
                     f"Etapa: {pipeline.STAGE_LABELS[before['stage']]} → {pipeline.STAGE_LABELS[new_stage]}",
                     actor_id, lost_reason)
    record(db, actor_id, "opportunity.stage", "opportunity", opp.id, before, snapshot(opp))
    db.commit()
    return opp


# ---------------------------------------------------------------- cotizaciones
def create_quote(db: Session, opp_id: str, items: list[dict], actor_id: str | None,
                 valid_days: int = 15) -> Quote:
    opp = get_or_404(db, Opportunity, opp_id, "Oportunidad")
    if opp.stage in pipeline.CLOSED_STAGES:
        raise DomainError("No se puede cotizar una oportunidad cerrada")
    if not items:
        raise DomainError("La cotización requiere al menos una partida")
    year = utcnow().year
    n = db.scalar(select(func.count()).select_from(Quote)) + 1
    q = Quote(opportunity_id=opp.id, folio=f"COT-{year}-{n:04d}", valid_until=utcnow() + timedelta(days=valid_days))
    for it in items:
        get_or_404(db, Product, it.get("product_id") or "", "Producto")
        qty, price = float(it.get("qty_kg") or 0), float(it.get("unit_price_mxn") or -1)
        if qty <= 0:
            raise DomainError("La cantidad (kg) debe ser mayor que cero")
        if price < 0:
            raise DomainError("El precio por kg no puede ser negativo")
        if it.get("packaging") not in PACKAGING:
            raise DomainError(f"Empaque inválido: {it.get('packaging')}")
        q.items.append(QuoteItem(product_id=it["product_id"], qty_kg=qty, packaging=it["packaging"],
                                 unit_price_mxn=price))
    opp.quotes.append(q)  # mantiene sincronizada la relación en memoria (ver bug corregido en VERIFICAR)
    db.flush()
    if opp.est_value_mxn is None:
        opp.est_value_mxn = q.total_mxn
    _system_activity(db, "opportunity", opp.id, f"Cotización {q.folio} creada ({q.total_kg:g} kg, ${q.total_mxn:,.2f})", actor_id)
    record(db, actor_id, "quote.create", "quote", q.id, after={"folio": q.folio, "total_mxn": q.total_mxn})
    db.commit()
    return q


# ---------------------------------------------------------------- actividades y tareas
def log_activity(db: Session, data: dict, actor_id: str | None) -> Activity:
    rtype, rid = data.get("related_type"), data.get("related_id")
    if rtype not in RELATED_MODELS:
        raise DomainError(f"Tipo relacionado inválido: {rtype}")
    get_or_404(db, RELATED_MODELS[rtype], rid or "", rtype)
    atype = data.get("type")
    if atype not in ACTIVITY_TYPES - {"sistema"}:
        raise DomainError(f"Tipo de actividad inválido: {atype}")
    subject = _clean(data.get("subject"))
    if not subject:
        raise DomainError("El asunto es obligatorio")
    a = Activity(type=atype, subject=subject, body=_clean(data.get("body")), related_type=rtype,
                 related_id=rid, actor_id=actor_id)
    db.add(a)
    db.flush()
    # Registrar contacto con un lead nuevo lo mueve a "contactado" (automatización ligera)
    if rtype == "lead" and atype in {"llamada", "correo", "whatsapp", "reunion"}:
        lead = db.get(Lead, rid)
        if lead.status == "nuevo":
            lead.status = "contactado"
            record(db, actor_id, "lead.status", "lead", lead.id, {"status": "nuevo"}, {"status": "contactado"},
                   summary="Automático: primer contacto registrado")
            for t in db.scalars(select(Task).where(Task.related_id == rid, Task.origin == "auto_lead",
                                                   Task.status == "pendiente")):
                t.status = "hecha"
    record(db, actor_id, "activity.create", "activity", a.id, after=snapshot(a))
    db.commit()
    return a


def create_task(db: Session, data: dict, actor_id: str | None, origin: str = "manual") -> Task:
    title = _clean(data.get("title"))
    if not title:
        raise DomainError("El título de la tarea es obligatorio")
    due = data.get("due_at")
    if isinstance(due, str) and due:
        due = datetime.fromisoformat(due)
    t = Task(title=title, due_at=due or None, priority=data.get("priority") or "media",
             assignee_id=data.get("assignee_id"), assignee_role=data.get("assignee_role"),
             related_type=data.get("related_type"), related_id=data.get("related_id"), origin=origin)
    db.add(t)
    db.flush()
    record(db, actor_id, "task.create", "task", t.id, after=snapshot(t))
    db.commit()
    return t


def complete_task(db: Session, task_id: str, actor_id: str | None) -> Task:
    t = get_or_404(db, Task, task_id, "Tarea")
    if t.status != "pendiente":
        raise DomainError("La tarea no está pendiente")
    before = snapshot(t)
    t.status = "hecha"
    record(db, actor_id, "task.complete", "task", t.id, before, snapshot(t))
    db.commit()
    return t


# ---------------------------------------------------------------- casos
def create_case(db: Session, data: dict, actor_id: str | None) -> Case:
    ctype = data.get("type")
    if ctype not in CASE_TYPES:
        raise DomainError(f"Tipo de caso inválido: {ctype}")
    sev = data.get("severity") or "media"
    if sev not in CASE_SEVERITIES:
        raise DomainError(f"Severidad inválida: {sev}")
    subject = _clean(data.get("subject"))
    if not subject:
        raise DomainError("El asunto del caso es obligatorio")
    if not (data.get("account_id") or data.get("lead_id")):
        raise DomainError("El caso debe ligarse a una cuenta o a un lead")
    n = db.scalar(select(func.count()).select_from(Case)) + 1
    c = Case(folio=f"CASO-{utcnow().year}-{n:04d}", type=ctype, severity=sev, subject=subject,
             description=_clean(data.get("description")), account_id=data.get("account_id"),
             contact_id=data.get("contact_id"), lead_id=data.get("lead_id"),
             lot_reference=_clean(data.get("lot_reference")), order_ref=_clean(data.get("order_ref")),
             owner_id=data.get("owner_id"), is_demo=bool(data.get("is_demo", False)))
    db.add(c)
    db.flush()
    owner_role = {"reclamacion_calidad": "calidad", "documentacion": "calidad", "entrega": "atencion",
                  "facturacion": "administracion"}.get(ctype, "atencion")
    db.add(Task(title=f"Atender {c.folio}: {subject}", assignee_role=owner_role, related_type="case",
                related_id=c.id, origin="auto_case", priority="alta" if sev in ("alta", "critica") else "media",
                due_at=add_business_hours(utcnow(), config.CASE_SLA_HOURS[sev])))
    record(db, actor_id, "case.create", "case", c.id, after=snapshot(c))
    db.commit()
    return c


def change_case_status(db: Session, case_id: str, new_status: str, actor_id: str | None,
                       lot_reference: str | None = None) -> Case:
    c = get_or_404(db, Case, case_id, "Caso")
    if new_status not in CASE_TRANSITIONS.get(c.status, set()):
        raise DomainError(f"Transición de caso no permitida: {c.status} → {new_status}")
    if _clean(lot_reference):
        c.lot_reference = _clean(lot_reference)
    if c.type == "reclamacion_calidad" and new_status in ("resuelto", "cerrado") and not c.lot_reference:
        raise DomainError("Una reclamación de calidad requiere número de lote para resolverse (trazabilidad FSSC 22000)")
    before = snapshot(c)
    c.status = new_status
    if new_status == "escalado_qms":
        db.add(IntegrationEvent(direction="out", system="qms", event_type="case.escalated",
                                payload={"case_id": c.id, "folio": c.folio, "lot": c.lot_reference}))
    _system_activity(db, "case", c.id, f"Estado: {before['status']} → {new_status}", actor_id)
    record(db, actor_id, "case.status", "case", c.id, before, snapshot(c))
    db.commit()
    return c


# ---------------------------------------------------------------- búsqueda
def search(db: Session, q: str, limit: int = 20) -> dict:
    q = (q or "").strip()
    if len(q) < 2:
        return {"leads": [], "accounts": [], "contacts": [], "opportunities": []}
    like = f"%{q.lower()}%"
    digits = "".join(ch for ch in q if ch.isdigit())
    lead_conds = [func.lower(Lead.full_name).like(like), func.lower(Lead.company_name).like(like),
                  func.lower(Lead.email).like(like)]
    contact_conds = [func.lower(Contact.full_name).like(like), func.lower(Contact.email).like(like)]
    if len(digits) >= 4:
        lead_conds.append(Lead.phone.like(f"%{digits}%"))
        contact_conds.append(Contact.phone.like(f"%{digits}%"))
    return {
        "leads": list(db.scalars(select(Lead).where(or_(*lead_conds)).limit(limit))),
        "accounts": list(db.scalars(select(Account).where(or_(func.lower(Account.name).like(like),
                                                              func.lower(Account.domain).like(like))).limit(limit))),
        "contacts": list(db.scalars(select(Contact).where(or_(*contact_conds)).limit(limit))),
        "opportunities": list(db.scalars(select(Opportunity).where(func.lower(Opportunity.title).like(like)).limit(limit))),
    }


def filter_leads(db: Session, status=None, sector=None, source=None, below_minimum=None):
    stmt = select(Lead).order_by(Lead.created_at.desc())
    if status:
        stmt = stmt.where(Lead.status == status)
    if sector:
        stmt = stmt.where(Lead.sector_code == sector)
    if source:
        stmt = stmt.where(Lead.source == source)
    if below_minimum is not None:
        stmt = stmt.where(Lead.below_minimum.is_(below_minimum))
    return list(db.scalars(stmt))


def timeline(db: Session, related_type: str, related_id: str) -> list[Activity]:
    return list(db.scalars(select(Activity).where(Activity.related_type == related_type,
                                                  Activity.related_id == related_id)
                           .order_by(Activity.occurred_at.desc())))


# ---------------------------------------------------------------- fusión de duplicados (RF-35)
MERGE_FIELDS = ["company_name", "email", "phone", "city", "state", "sector_code", "product_interest_text",
                "est_volume_kg", "campaign", "message"]


def merge_leads(db: Session, keep_id: str, dup_id: str, actor_id: str | None) -> Lead:
    """Fusiona `dup` en `keep`: completa campos vacíos, mueve interacciones, tareas, casos y vínculos de
    correo, y deja `dup` descartado con referencia (no se borra: trazabilidad)."""
    if keep_id == dup_id:
        raise DomainError("No se puede fusionar un lead consigo mismo")
    keep, dup = get_or_404(db, Lead, keep_id, "Lead"), get_or_404(db, Lead, dup_id, "Lead")
    for lead in (keep, dup):
        if lead.status == "convertido":
            raise DomainError(f"El lead {lead.full_name} ya fue convertido; fusiona desde la cuenta")
        if lead.merged_into_id:
            raise DomainError(f"El lead {lead.full_name} ya fue fusionado")
    before_keep, before_dup = snapshot(keep), snapshot(dup)
    filled = []
    for f in MERGE_FIELDS:
        if getattr(keep, f) in (None, "") and getattr(dup, f) not in (None, ""):
            if f == "email" and db.scalar(select(Lead).where(Lead.email == dup.email, Lead.id != dup.id)):
                continue
            setattr(keep, f, getattr(dup, f))
            filled.append(f)
    if filled and "est_volume_kg" in filled:
        keep.volume_band = _band_from_kg(keep.est_volume_kg)
        keep.below_minimum = keep.volume_band == "menor_500kg"
    moved = {"activities": 0, "tasks": 0, "cases": 0, "emails": 0}
    for a in db.scalars(select(Activity).where(Activity.related_type == "lead", Activity.related_id == dup.id)):
        a.related_id = keep.id
        moved["activities"] += 1
    for t in db.scalars(select(Task).where(Task.related_type == "lead", Task.related_id == dup.id)):
        if t.origin == "auto_lead" and t.status == "pendiente":
            t.status = "cancelada"  # ya existe la tarea de primer contacto del lead que se conserva
        else:
            t.related_id = keep.id
            moved["tasks"] += 1
    for c in db.scalars(select(Case).where(Case.lead_id == dup.id)):
        c.lead_id = keep.id
        moved["cases"] += 1
    from app.models import EmailClassification  # import local para evitar ciclo conceptual
    for ec in db.scalars(select(EmailClassification).where(EmailClassification.crm_link_id == dup.id)):
        ec.crm_link_id = keep.id
        ec.crm_links = {**(ec.crm_links or {}), "lead": keep.id}
        moved["emails"] += 1
    for other in db.scalars(select(Lead).where(Lead.possible_duplicate_of_id == dup.id)):
        other.possible_duplicate_of_id = keep.id
    if keep.possible_duplicate_of_id == dup.id:
        keep.possible_duplicate_of_id, keep.duplicate_reason = None, None
    dup.merged_into_id = keep.id
    dup.status = "descartado"
    dup.discard_reason = f"Fusionado con {keep.full_name} ({keep.id[:8]})"
    dup.possible_duplicate_of_id = None
    db.add(Activity(type="sistema", subject=f"Fusión: se integró el lead {dup.full_name}",
                    body=f"Campos completados: {', '.join(filled) or 'ninguno'} · movidos: {moved}",
                    related_type="lead", related_id=keep.id, actor_id=actor_id))
    record(db, actor_id, "lead.merge", "lead", keep.id, before_keep, snapshot(keep))
    record(db, actor_id, "lead.merged_into", "lead", dup.id, before_dup, snapshot(dup))
    db.commit()
    return keep


# ---------------------------------------------------------------- estado de cotización
QUOTE_TRANSITIONS = {"borrador": {"enviada", "rechazada"}, "enviada": {"aceptada", "rechazada", "vencida"},
                     "aceptada": set(), "rechazada": set(), "vencida": {"enviada"}}


def change_quote_status(db: Session, quote_id: str, new_status: str, actor_id: str | None) -> Quote:
    """'enviada' solo registra que una persona la envió por su cuenta: el CRM no envía correos."""
    q = get_or_404(db, Quote, quote_id, "Cotización")
    if new_status not in QUOTE_TRANSITIONS.get(q.status, set()):
        raise DomainError(f"Transición de cotización no permitida: {q.status} → {new_status}")
    before = snapshot(q)
    q.status = new_status
    if new_status == "enviada":
        q.sent_at = utcnow()
        db.add(Task(title=f"Seguimiento a cotización {q.folio}", assignee_role="ventas", related_type="opportunity",
                    related_id=q.opportunity_id, origin="auto_quote", due_at=add_business_hours(utcnow(), 27)))
    _system_activity(db, "opportunity", q.opportunity_id, f"Cotización {q.folio}: {before['status']} → {new_status}", actor_id)
    record(db, actor_id, "quote.status", "quote", q.id, before, snapshot(q))
    db.commit()
    return q
