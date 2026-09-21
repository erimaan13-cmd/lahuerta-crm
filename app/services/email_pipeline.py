"""Orquestación: INGESTA → NORMALIZACIÓN → CLASIFICACIÓN → EXTRACCIÓN → VINCULACIÓN CRM →
ENRUTAMIENTO (sugerencia) → REVISIÓN HUMANA. Ninguna acción irreversible es automática (D-12)."""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.audit import record, snapshot
from app.classifier import engine, normalize, taxonomy
from app.classifier.extract import CatalogItem
from app.classifier.llm import LLMClient
from app.integrations.email_providers import EmailProvider, RawEmail
from app.models import (Account, Activity, Case, Contact, EmailClassification, EmailMessage, Lead,
                        OrderReference, Product, Quote, Task, utcnow)
from app.services import crm
from app.services.common import DomainError, email_domain, get_or_404

log = logging.getLogger("crm.email")


def _catalog(db: Session) -> list[CatalogItem]:
    return [CatalogItem(p.id, p.sku, p.name, [k for k in (p.keywords or "").split(",")])
            for p in db.scalars(select(Product).where(Product.is_active.is_(True)))]


def resolve_sender(db: Session, from_email: str) -> tuple[str, dict]:
    """Identidad del remitente (dimensión ortogonal a la categoría, D-06)."""
    links: dict = {}
    c = db.scalar(select(Contact).where(Contact.email == from_email))
    if c:
        links.update(contact=c.id, account=c.account_id)
        return "contacto", links
    lead = db.scalar(select(Lead).where(Lead.email == from_email))
    if lead:
        links["lead"] = lead.id
        if lead.converted_account_id:
            links["account"] = lead.converted_account_id
        return "lead", links
    dom = email_domain(from_email)
    if dom and dom in config.SUPPLIER_DOMAINS:
        return "proveedor", links
    if dom:
        acc = db.scalar(select(Account).where(Account.domain == dom))
        if acc:
            links["account"] = acc.id
            return "cuenta_dominio", links
    return "desconocido", links


def link_references(db: Session, ents: dict, links: dict) -> dict:
    refs = ents.get("references", {})
    for folio in refs.get("quote_folio", []):
        q = db.scalar(select(Quote).where(Quote.folio == folio))
        if q:
            links["quote"] = q.id
            links["opportunity"] = q.opportunity_id
            links.setdefault("account", q.opportunity.account_id)
    for folio in refs.get("case_folio", []):
        c = db.scalar(select(Case).where(Case.folio == folio))
        if c:
            links["case"] = c.id
    for oref in refs.get("order_ref", []):
        o = db.scalar(select(OrderReference).where(OrderReference.erp_order_id == oref))
        if o:
            links["order"] = o.id
            links.setdefault("account", o.account_id)
    for lot in refs.get("lot_ref", []):
        c = db.scalar(select(Case).where(Case.lot_reference == lot))
        if c:
            links.setdefault("case", c.id)
    return links


_LINK_PRIORITY = ["case", "opportunity", "order", "contact", "account", "lead"]


def primary_link(links: dict) -> tuple[str | None, str | None]:
    for k in _LINK_PRIORITY:
        if links.get(k):
            return k, links[k]
    return None, None


def process_raw(db: Session, raw: RawEmail, llm: LLMClient | None = None,
                actor_id: str | None = None) -> tuple[EmailMessage, bool]:
    """Procesa un correo. Idempotente por (provider, message_id). Devuelve (mensaje, nuevo)."""
    existing = db.scalar(select(EmailMessage).where(EmailMessage.provider == raw.provider,
                                                    EmailMessage.provider_message_id == raw.message_id))
    if existing:
        return existing, False
    if not raw.from_email or "@" not in raw.from_email:
        raise DomainError(f"Correo sin remitente válido: {raw.message_id}")

    body_clean = normalize.clean_body(raw.body)
    msg = EmailMessage(provider=raw.provider, provider_message_id=raw.message_id, thread_id=raw.thread_id,
                       from_email=raw.from_email.lower(), from_name=raw.from_name, to=raw.to,
                       subject=raw.subject or "", body_text=raw.body or "", body_clean=body_clean,
                       received_at=raw.received_at or utcnow(), has_attachments=raw.has_attachments,
                       raw_hash=raw.raw_hash, is_demo=raw.is_demo)
    db.add(msg)
    db.flush()

    sender_kind, links = resolve_sender(db, msg.from_email)
    result = engine.classify(engine.ClassifierInput(subject=msg.subject, body=raw.body or "",
                                                    from_email=msg.from_email, from_name=msg.from_name,
                                                    sender_kind=sender_kind, catalog=_catalog(db)), llm=llm)
    links = link_references(db, result.extracted_entities, links)
    ltype, lid = primary_link(links)
    ents = dict(result.extracted_entities, sender_kind=sender_kind, rule_evidence=result.evidence)
    if links.get("account"):  # el CRM es la fuente de verdad del nombre de la empresa
        acc = db.get(Account, links["account"])
        ents.update(company=acc.name, company_source="crm")
    cls = EmailClassification(
        email_id=msg.id, category=result.classification, confidence=result.confidence, margin=result.margin,
        method=result.method, scores=result.scores, extracted_entities=ents,
        suggested_owner_role=result.suggested_owner, suggested_action=result.suggested_action,
        suggested_action_label=result.suggested_action_label, crm_link_type=ltype, crm_link_id=lid,
        crm_links=links, review_status="needs_review" if result.needs_review else "auto",
        review_reason=result.review_reason, classifier_version=result.version)
    db.add(cls)
    # Vincular (reversible): la interacción aparece en la línea de tiempo de la entidad
    if ltype in ("lead", "account", "contact", "opportunity", "case"):
        db.add(Activity(type="correo", subject=f"Correo recibido: {msg.subject[:150]}",
                        body=body_clean[:2000], related_type=ltype, related_id=lid))
    record(db, actor_id, "email.classify", "email", msg.id,
           after={"category": cls.category, "confidence": cls.confidence, "review": cls.review_status})
    db.commit()
    log.info("email_classified", extra={"email_id": msg.id, "category": cls.category,
                                        "confidence": cls.confidence, "review": cls.review_status})
    return msg, True


def ingest(db: Session, provider: EmailProvider, llm: LLMClient | None = None,
           actor_id: str | None = None) -> dict:
    stats = {"fetched": 0, "new": 0, "duplicates": 0, "errors": 0, "needs_review": 0, "auto": 0, "error_details": []}
    for raw in provider.fetch():
        stats["fetched"] += 1
        try:
            msg, new = process_raw(db, raw, llm, actor_id)
        except DomainError as e:
            db.rollback()
            stats["errors"] += 1
            stats["error_details"].append(e.message)
            continue
        if not new:
            stats["duplicates"] += 1
            continue
        stats["new"] += 1
        stats[msg.classification.review_status] += 1
    stats["error_details"] = stats["error_details"][:20]
    return stats


# ---------------------------------------------------------------- revisión humana
def review(db: Session, email_id: str, actor_id: str, category: str | None = None) -> EmailClassification:
    """Confirma la categoría propuesta o la corrige. La corrección queda como etiqueta auditada."""
    msg = get_or_404(db, EmailMessage, email_id, "Correo")
    cls = msg.classification
    if cls.review_status == "aplicado":
        raise DomainError("La sugerencia ya fue aplicada")
    if category and category not in taxonomy.CATEGORIES:
        raise DomainError(f"Categoría inválida: {category}")
    before = snapshot(cls)
    final = category or cls.category
    cls.final_category = final
    cls.review_status = "corregido" if final != cls.category else "confirmado"
    cls.reviewed_by = actor_id
    meta = taxonomy.CATEGORIES[final]
    cls.suggested_owner_role = meta["owner"]
    cls.suggested_action, cls.suggested_action_label = meta["action"], meta["action_label"]
    if cls.extracted_entities.get("sender_kind") == "desconocido" and final in taxonomy.NEW_SENDER_ACTION_OVERRIDE:
        cls.suggested_action, cls.suggested_action_label = taxonomy.NEW_SENDER_ACTION_OVERRIDE[final]
    record(db, actor_id, "email.review", "email_classification", cls.id, before, snapshot(cls))
    db.commit()
    return cls


def apply_suggestion(db: Session, email_id: str, actor_id: str, action: str | None = None) -> dict:
    """Ejecuta la acción sugerida (o la elegida) SOLO por decisión humana."""
    msg = get_or_404(db, EmailMessage, email_id, "Correo")
    cls = msg.classification
    if cls.review_status == "needs_review":
        raise DomainError("Primero confirma o corrige la categoría (bandeja Needs Review)")
    if cls.review_status == "aplicado":
        raise DomainError("La sugerencia ya fue aplicada")
    action = action or cls.suggested_action
    if action not in taxonomy.ACTIONS:
        raise DomainError(f"Acción inválida: {action}")
    category = cls.final_category or cls.category
    ents, links = cls.extracted_entities, dict(cls.crm_links or {})
    result: dict = {"action": action}

    if action == "crear_lead":
        prod_names = ", ".join(p["name"] for p in ents.get("products", [])) or None
        lead, created = crm.create_lead(db, {
            "full_name": ents.get("sender_name") or msg.from_email.split("@")[0],
            "email": msg.from_email, "phone": (ents.get("phones") or [None])[0],
            "company_name": ents.get("company"), "city": ents.get("city"), "state": ents.get("state"),
            "sector_code": ents.get("sector"), "product_interest_text": prod_names,
            "est_volume_kg": ents.get("total_kg"), "message": msg.body_clean[:2000], "source": "email",
            "is_demo": msg.is_demo, "consent_source": "correo entrante",
        }, actor_id)
        links["lead"] = lead.id
        result.update(entity_type="lead", entity_id=lead.id, created=created)
    elif action == "crear_tarea":
        ltype, lid = primary_link(links)
        t = crm.create_task(db, {"title": f"[{taxonomy.CATEGORIES[category]['label']}] {msg.subject[:150]}",
                                 "assignee_role": cls.suggested_owner_role, "related_type": ltype,
                                 "related_id": lid, "priority": "alta" if ents.get("urgency") == "alta" else "media"},
                            actor_id, origin="sugerencia_correo")
        result.update(entity_type="task", entity_id=t.id)
    elif action == "abrir_caso":
        if not (links.get("account") or links.get("lead")):
            raise DomainError("El remitente no está vinculado a una cuenta o lead: crea el lead primero")
        refs = ents.get("references", {})
        case = crm.create_case(db, {
            "type": "reclamacion_calidad" if category == "CALIDAD_RECLAMACION" else "documentacion"
            if category == "DOCUMENTACION_CALIDAD" else "otro",
            "severity": "alta" if category == "CALIDAD_RECLAMACION" else "baja",
            "subject": msg.subject[:200] or "(sin asunto)", "description": msg.body_clean[:4000],
            "account_id": links.get("account"), "contact_id": links.get("contact"), "lead_id": links.get("lead"),
            "lot_reference": (refs.get("lot_ref") or [None])[0], "order_ref": (refs.get("order_ref") or [None])[0],
            "is_demo": msg.is_demo}, actor_id)
        links["case"] = case.id
        result.update(entity_type="case", entity_id=case.id)
    elif action == "registrar_actividad":
        ltype, lid = primary_link(links)
        if not ltype or ltype == "order":
            raise DomainError("No hay entidad CRM vinculada para registrar la interacción")
        result.update(entity_type=ltype, entity_id=lid, note="La interacción ya quedó en la línea de tiempo")
    # reenviar_fuera_crm / ignorar / revisar: solo cambian el estado; no se envía nada

    before = snapshot(cls)
    cls.review_status = "aplicado"
    cls.applied_entity_type, cls.applied_entity_id = result.get("entity_type"), result.get("entity_id")
    cls.crm_links = links
    cls.crm_link_type, cls.crm_link_id = primary_link(links)
    cls.reviewed_by = cls.reviewed_by or actor_id
    record(db, actor_id, "email.apply", "email_classification", cls.id, before, snapshot(cls))
    db.commit()
    return result


def needs_review_queue(db: Session) -> list[EmailMessage]:
    return list(db.scalars(select(EmailMessage).join(EmailClassification)
                           .where(EmailClassification.review_status == "needs_review")
                           .order_by(EmailMessage.received_at.desc())))


def pending_tasks_for_role(db: Session, role: str) -> list[Task]:
    return list(db.scalars(select(Task).where(Task.status == "pendiente", Task.assignee_role == role)))
