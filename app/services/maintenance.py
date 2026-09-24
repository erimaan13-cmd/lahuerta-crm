"""Mantenimiento de activos (E-10): "asignar objeto", "asignar mantenimiento del objeto" y
"asignar frecuencia", más la ficha del activo con sus documentos y su responsable.

Decisiones que implementa:
- La frecuencia puede ser por días, por kilómetros o por horas de uso, y **vence lo que ocurra
  primero**: un camión que rueda mucho llega a los 10 000 km antes de los 6 meses.
- El odómetro (u horas) es el dato que dispara los vencimientos, por eso se captura aparte y solo
  puede subir: un kilometraje menor al registrado casi siempre es un error de dedo.
- Al cerrar una orden que viene de un plan, se recalcula el siguiente vencimiento desde lo que de
  verdad se hizo (fecha y odómetro reales), no desde la fecha programada.
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import config
from app.audit import record, snapshot
from app.models import Asset, Employee, MaintenancePlan, User, WorkOrder, utcnow
from app.services import inventory
from app.services.business_time import to_local
from app.services.common import DomainError, get_or_404
from app.services.files import parse_date

TYPES = {"camion": "Camión", "clima": "Clima", "equipo": "Equipo", "otro": "Otro"}
STATUSES = {"activo": "Activo", "reparacion": "En reparación", "baja": "Baja"}
PLAN_KINDS = {"preventivo": "Preventivo", "verificacion": "Verificación", "otro": "Otro"}
WO_KINDS = {"preventivo": "Preventivo", "correctivo": "Correctivo"}
WO_STATUSES = {"abierta": "Abierta", "en_proceso": "En proceso", "cerrada": "Cerrada",
               "cancelada": "Cancelada"}
PROVIDERS = {"interno": "Taller interno", "externo": "Proveedor externo"}
OPEN_WO = ("abierta", "en_proceso")


def _clean(v):
    return v.strip() if isinstance(v, str) and v.strip() else (None if isinstance(v, str) else v)


def _days_left(when) -> int:
    return (to_local(when).date() - to_local(utcnow()).date()).days


# ------------------------------------------------------------------ activos ("asignar objeto")
def create_asset(db: Session, data: dict, actor_id: str | None) -> Asset:
    code = (data.get("code") or "").strip().upper()
    name = _clean(data.get("name"))
    if not code or not name:
        raise DomainError("El activo necesita clave y nombre")
    if db.scalar(select(Asset).where(Asset.code == code)):
        raise DomainError(f"Ya existe un activo con la clave {code}")
    atype = data.get("type") or "equipo"
    if atype not in TYPES:
        raise DomainError(f"Tipo de activo no válido: {atype}")
    asset = Asset(code=code[:30], name=name[:160], type=atype, brand=_clean(data.get("brand")),
                  model=_clean(data.get("model")), identifier=_clean(data.get("identifier")),
                  location=_clean(data.get("location")), notes=_clean(data.get("notes")),
                  purchased_on=parse_date(data.get("purchased_on")),
                  odometer_km=inventory.num(data.get("odometer_km"), "el kilometraje", required=False, minimum=0),
                  hours_used=inventory.num(data.get("hours_used"), "las horas de uso", required=False, minimum=0),
                  is_demo=bool(data.get("is_demo", False)))
    if data.get("assigned_user_id"):
        asset.assigned_user_id = get_or_404(db, User, data["assigned_user_id"], "Usuario").id
    if data.get("assigned_employee_id"):
        asset.assigned_employee_id = get_or_404(db, Employee, data["assigned_employee_id"], "Empleado").id
    db.add(asset)
    db.flush()
    record(db, actor_id, "activo.alta", "asset", asset.id,
           after={"clave": asset.code, "nombre": asset.name, "tipo": asset.type,
                  "identificador": asset.identifier, "km": asset.odometer_km, "horas": asset.hours_used},
           summary=f"Activo dado de alta: {asset.code} — {asset.name}")
    db.commit()
    return asset


def update_asset(db: Session, asset_id: str, data: dict, actor_id: str | None) -> Asset:
    """Actualiza datos del activo, incluidos odómetro y horas (lo que dispara los vencimientos)."""
    asset = get_or_404(db, Asset, asset_id, "Activo")
    before = snapshot(asset)
    for field in ("name", "brand", "model", "identifier", "location", "notes"):
        if data.get(field) not in (None, ""):
            setattr(asset, field, _clean(data[field]))
    if data.get("type"):
        if data["type"] not in TYPES:
            raise DomainError(f"Tipo de activo no válido: {data['type']}")
        asset.type = data["type"]
    if data.get("purchased_on"):
        asset.purchased_on = parse_date(data["purchased_on"])
    km = inventory.num(data.get("odometer_km"), "el kilometraje", required=False, minimum=0)
    if km is not None:
        if asset.odometer_km is not None and km < asset.odometer_km:
            raise DomainError(f"El kilometraje no puede bajar: el activo registra {asset.odometer_km:g} km "
                              f"y se capturaron {km:g} km")
        asset.odometer_km = km
    horas = inventory.num(data.get("hours_used"), "las horas de uso", required=False, minimum=0)
    if horas is not None:
        if asset.hours_used is not None and horas < asset.hours_used:
            raise DomainError(f"Las horas de uso no pueden bajar: el activo registra {asset.hours_used:g} h "
                              f"y se capturaron {horas:g} h")
        asset.hours_used = horas
    record(db, actor_id, "activo.cambio", "asset", asset.id, before, snapshot(asset),
           summary=f"Activo actualizado: {asset.code}")
    db.commit()
    return asset


def assign(db: Session, asset_id: str, actor_id: str | None, user_id: str | None = None,
           employee_id: str | None = None) -> Asset:
    """Asigna el activo a un usuario del sistema o a un empleado del expediente de RRHH."""
    asset = get_or_404(db, Asset, asset_id, "Activo")
    if not user_id and not employee_id:
        raise DomainError("Indica a quién se asigna el activo")
    before = snapshot(asset)
    quien = []
    if user_id:
        u = get_or_404(db, User, user_id, "Usuario")
        asset.assigned_user_id = u.id
        quien.append(u.full_name)
    if employee_id:
        e = get_or_404(db, Employee, employee_id, "Empleado")
        asset.assigned_employee_id = e.id
        quien.append(e.full_name)
    record(db, actor_id, "activo.asignado", "asset", asset.id, before, snapshot(asset),
           summary=f"Activo {asset.code} asignado a {', '.join(quien)}")
    db.commit()
    return asset


def set_status(db: Session, asset_id: str, status: str, actor_id: str | None) -> Asset:
    asset = get_or_404(db, Asset, asset_id, "Activo")
    if status not in STATUSES:
        raise DomainError(f"Estado de activo no válido: {status}")
    before = snapshot(asset)
    asset.status = status
    record(db, actor_id, "activo.estado", "asset", asset.id, before, snapshot(asset),
           summary=f"Activo {asset.code}: {STATUSES[status]}")
    db.commit()
    return asset


# ------------------------------------------------------------------ planes ("asignar frecuencia")
def _recalc(plan: MaintenancePlan, asset: Asset) -> None:
    """Recalcula los vencimientos desde lo último hecho (o desde la fecha/odómetro actuales)."""
    if plan.freq_days:
        base = plan.last_done_on or utcnow()
        plan.next_due_on = base + timedelta(days=int(plan.freq_days))
    if plan.freq_km:
        base = plan.last_done_km if plan.last_done_km is not None else (asset.odometer_km or 0.0)
        plan.next_due_km = round(base + plan.freq_km, 2)
    if plan.freq_hours:
        base = plan.last_done_hours if plan.last_done_hours is not None else (asset.hours_used or 0.0)
        plan.next_due_hours = round(base + plan.freq_hours, 2)


def create_plan(db: Session, asset_id: str, data: dict, actor_id: str | None) -> MaintenancePlan:
    asset = get_or_404(db, Asset, asset_id, "Activo")
    name = _clean(data.get("name"))
    if not name:
        raise DomainError("El mantenimiento necesita un nombre (por ejemplo: cambio de aceite)")
    kind = data.get("kind") or "preventivo"
    if kind not in PLAN_KINDS:
        raise DomainError(f"Tipo de mantenimiento no válido: {kind}")
    days = inventory.num(data.get("freq_days"), "la frecuencia en días", required=False, minimum=1)
    km = inventory.num(data.get("freq_km"), "la frecuencia en kilómetros", required=False, minimum=1)
    hours = inventory.num(data.get("freq_hours"), "la frecuencia en horas", required=False, minimum=1)
    if not any((days, km, hours)):
        raise DomainError("Define al menos una frecuencia: días, kilómetros u horas de uso")
    plan = MaintenancePlan(asset_id=asset.id, name=name[:160], kind=kind,
                           freq_days=int(days) if days else None, freq_km=km, freq_hours=hours,
                           last_done_on=parse_date(data.get("last_done_on")),
                           last_done_km=inventory.num(data.get("last_done_km"), "el kilometraje del último servicio",
                                                      required=False, minimum=0),
                           last_done_hours=inventory.num(data.get("last_done_hours"), "las horas del último servicio",
                                                         required=False, minimum=0))
    if data.get("assignee_user_id"):
        plan.assignee_user_id = get_or_404(db, User, data["assignee_user_id"], "Usuario").id
    _recalc(plan, asset)
    db.add(plan)
    db.flush()
    record(db, actor_id, "mantenimiento.plan", "asset", asset.id,
           after={"plan_id": plan.id, "nombre": plan.name, "cada_dias": plan.freq_days, "cada_km": plan.freq_km,
                  "cada_horas": plan.freq_hours,
                  "proximo_en": plan.next_due_on.date().isoformat() if plan.next_due_on else None,
                  "proximo_km": plan.next_due_km, "proximo_horas": plan.next_due_hours},
           summary=f"Plan «{plan.name}» asignado a {asset.code}")
    db.commit()
    return plan


def set_plan_active(db: Session, plan_id: str, active: bool, actor_id: str | None) -> MaintenancePlan:
    plan = get_or_404(db, MaintenancePlan, plan_id, "Plan de mantenimiento")
    before = snapshot(plan)
    plan.is_active = active
    record(db, actor_id, "mantenimiento.plan_estado", "asset", plan.asset_id, before, snapshot(plan),
           summary=f"Plan «{plan.name}» {'activado' if active else 'desactivado'}")
    db.commit()
    return plan


# ------------------------------------------------------------------ órdenes de mantenimiento
def create_work_order(db: Session, data: dict, actor_id: str | None) -> WorkOrder:
    asset = get_or_404(db, Asset, data.get("asset_id") or "", "Activo")
    description = _clean(data.get("description"))
    if not description:
        raise DomainError("Describe el trabajo a realizar")
    kind = data.get("kind") or "preventivo"
    if kind not in WO_KINDS:
        raise DomainError(f"Tipo de orden no válido: {kind}")
    provider = data.get("provider") or "interno"
    if provider not in PROVIDERS:
        raise DomainError(f"Proveedor no válido: {provider}")
    provider_name = _clean(data.get("provider_name"))
    if provider == "externo" and not provider_name:
        raise DomainError("Indica el nombre del proveedor externo")
    plan = None
    if data.get("plan_id"):
        plan = get_or_404(db, MaintenancePlan, data["plan_id"], "Plan de mantenimiento")
        if plan.asset_id != asset.id:
            raise DomainError(f"El plan «{plan.name}» no pertenece al activo {asset.code}")
    n = db.scalar(select(func.count()).select_from(WorkOrder)) + 1
    wo = WorkOrder(folio=f"OM-{n:04d}", asset_id=asset.id, plan_id=plan.id if plan else None, kind=kind,
                   description=description[:300], provider=provider, provider_name=provider_name,
                   notes=_clean(data.get("notes")), is_demo=bool(data.get("is_demo", False)))
    if data.get("assignee_user_id"):
        wo.assignee_user_id = get_or_404(db, User, data["assignee_user_id"], "Usuario").id
    db.add(wo)
    db.flush()
    record(db, actor_id, "orden_mantenimiento.alta", "work_order", wo.id,
           after={"folio": wo.folio, "activo": asset.code, "tipo": wo.kind, "proveedor": wo.provider,
                  "plan": plan.name if plan else None, "descripcion": wo.description},
           summary=f"Orden {wo.folio} ({WO_KINDS[kind]}) para {asset.code}")
    db.commit()
    return wo


def close_work_order(db: Session, wo_id: str, data: dict, actor_id: str | None) -> WorkOrder:
    """Cierra la orden, sube el odómetro del activo si procede y recorre el siguiente vencimiento."""
    wo = get_or_404(db, WorkOrder, wo_id, "Orden de mantenimiento")
    if wo.status not in OPEN_WO:
        raise DomainError(f"La orden {wo.folio} ya está {WO_STATUSES.get(wo.status, wo.status).lower()}")
    asset = wo.asset
    before_wo, before_asset = snapshot(wo), snapshot(asset)
    wo.cost_mxn = inventory.num(data.get("cost_mxn"), "el costo", required=False, minimum=0)
    wo.done_on = parse_date(data.get("done_on")) or utcnow()
    wo.odometer_km = inventory.num(data.get("odometer_km"), "el kilometraje", required=False, minimum=0)
    wo.hours_used = inventory.num(data.get("hours_used"), "las horas de uso", required=False, minimum=0)
    if data.get("notes"):
        wo.notes = _clean(data["notes"])
    wo.status = "cerrada"
    # El odómetro del activo solo sube: si el capturado es menor, se respeta el del activo.
    if wo.odometer_km is not None and (asset.odometer_km is None or wo.odometer_km > asset.odometer_km):
        asset.odometer_km = wo.odometer_km
    if wo.hours_used is not None and (asset.hours_used is None or wo.hours_used > asset.hours_used):
        asset.hours_used = wo.hours_used
    plan = wo.plan
    if plan:
        plan.last_done_on = wo.done_on
        plan.last_done_km = wo.odometer_km if wo.odometer_km is not None else asset.odometer_km
        plan.last_done_hours = wo.hours_used if wo.hours_used is not None else asset.hours_used
        _recalc(plan, asset)
    record(db, actor_id, "orden_mantenimiento.cierre", "work_order", wo.id, before_wo,
           {**snapshot(wo), "activo_km": asset.odometer_km, "activo_horas": asset.hours_used,
            "proximo_en": plan.next_due_on.date().isoformat() if plan and plan.next_due_on else None,
            "proximo_km": plan.next_due_km if plan else None,
            "proximo_horas": plan.next_due_hours if plan else None},
           summary=f"Orden {wo.folio} cerrada" + (f" · costo ${wo.cost_mxn:,.2f}" if wo.cost_mxn else ""))
    if before_asset != snapshot(asset):
        record(db, actor_id, "activo.cambio", "asset", asset.id, before_asset, snapshot(asset),
               summary=f"Lectura actualizada al cerrar {wo.folio}")
    db.commit()
    return wo


def cancel_work_order(db: Session, wo_id: str, actor_id: str | None, motivo: str | None = None) -> WorkOrder:
    wo = get_or_404(db, WorkOrder, wo_id, "Orden de mantenimiento")
    if wo.status not in OPEN_WO:
        raise DomainError(f"La orden {wo.folio} ya está {WO_STATUSES.get(wo.status, wo.status).lower()}")
    if not _clean(motivo):
        raise DomainError("Para cancelar una orden indica el motivo")
    before = snapshot(wo)
    wo.status = "cancelada"
    wo.notes = f"{wo.notes + chr(10) if wo.notes else ''}Cancelada: {_clean(motivo)}"
    record(db, actor_id, "orden_mantenimiento.cancelada", "work_order", wo.id, before, snapshot(wo),
           summary=f"Orden {wo.folio} cancelada: {_clean(motivo)}")
    db.commit()
    return wo


# ------------------------------------------------------------------ vencimientos y consultas
def plan_state(plan: MaintenancePlan, asset: Asset) -> dict:
    """Estado de un plan: vence lo que ocurra primero (fecha, kilómetros u horas)."""
    razones, estado = [], None
    dias = km_faltantes = horas_faltantes = None
    if plan.next_due_on:
        dias = _days_left(plan.next_due_on)
        if dias < 0:
            razones.append(f"vencido por fecha hace {-dias} días")
            estado = "vencido"
        elif dias <= config.MAINT_ALERT_DAYS:
            razones.append(f"vence en {dias} días")
            estado = estado or "proximo"
    if plan.next_due_km is not None and asset.odometer_km is not None:
        km_faltantes = round(plan.next_due_km - asset.odometer_km, 2)
        if km_faltantes < 0:
            razones.append(f"vencido por kilometraje ({-km_faltantes:g} km de más)")
            estado = "vencido"
        elif km_faltantes <= config.MAINT_ALERT_KM:
            razones.append(f"faltan {km_faltantes:g} km")
            estado = estado or "proximo"
    if plan.next_due_hours is not None and asset.hours_used is not None:
        horas_faltantes = round(plan.next_due_hours - asset.hours_used, 2)
        if horas_faltantes < 0:
            razones.append(f"vencido por horas ({-horas_faltantes:g} h de más)")
            estado = "vencido"
        elif horas_faltantes <= config.MAINT_ALERT_HOURS:
            razones.append(f"faltan {horas_faltantes:g} h")
            estado = estado or "proximo"
    return {"plan": plan, "asset": asset, "estado": estado, "razones": razones, "dias": dias,
            "km_faltantes": km_faltantes, "horas_faltantes": horas_faltantes}


def due_plans(db: Session) -> list[dict]:
    """Planes vencidos o próximos (primero los vencidos). Usa los umbrales de config."""
    out = []
    for plan in db.scalars(select(MaintenancePlan).where(MaintenancePlan.is_active.is_(True))):
        asset = plan.asset
        if asset.status == "baja":
            continue  # un activo dado de baja ya no genera pendientes
        state = plan_state(plan, asset)
        if state["estado"]:
            out.append(state)
    out.sort(key=lambda s: (s["estado"] != "vencido", s["dias"] if s["dias"] is not None else 9999))
    return out


def assets(db: Session, type: str | None = None, status: str | None = None) -> list[Asset]:
    stmt = select(Asset).order_by(Asset.code)
    if type:
        stmt = stmt.where(Asset.type == type)
    if status:
        stmt = stmt.where(Asset.status == status)
    return list(db.scalars(stmt))


def work_orders(db: Session, status: str | None = None, asset_id: str | None = None) -> list[WorkOrder]:
    stmt = select(WorkOrder).order_by(WorkOrder.created_at.desc())
    if status:
        stmt = stmt.where(WorkOrder.status == status)
    if asset_id:
        stmt = stmt.where(WorkOrder.asset_id == asset_id)
    return list(db.scalars(stmt))


def metrics(db: Session, period_days: int = 365) -> dict:
    """Activos por tipo y estado, pendientes, costo por activo y costo del periodo, órdenes abiertas."""
    todos = list(db.scalars(select(Asset)))
    por_tipo, por_estado = {}, {}
    for a in todos:
        por_tipo[TYPES.get(a.type, a.type)] = por_tipo.get(TYPES.get(a.type, a.type), 0) + 1
        por_estado[STATUSES.get(a.status, a.status)] = por_estado.get(STATUSES.get(a.status, a.status), 0) + 1
    desde = utcnow() - timedelta(days=period_days)
    costo_por_activo: dict[str, float] = {}
    total = 0.0
    for wo in db.scalars(select(WorkOrder).where(WorkOrder.status == "cerrada", WorkOrder.cost_mxn.is_not(None))):
        if wo.done_on and wo.done_on < desde:
            continue
        total += wo.cost_mxn
        clave = f"{wo.asset.code} — {wo.asset.name}"
        costo_por_activo[clave] = round(costo_por_activo.get(clave, 0.0) + wo.cost_mxn, 2)
    pendientes = due_plans(db)
    return {
        "activos": len(todos), "por_tipo": por_tipo, "por_estado": por_estado,
        "vencidos": sum(1 for p in pendientes if p["estado"] == "vencido"),
        "proximos": sum(1 for p in pendientes if p["estado"] == "proximo"),
        "ordenes_abiertas": db.scalar(select(func.count()).select_from(WorkOrder)
                                      .where(WorkOrder.status.in_(OPEN_WO))) or 0,
        "costo_periodo_mxn": round(total, 2), "periodo_dias": period_days,
        "costo_por_activo": [{"activo": k, "mxn": v} for k, v in
                             sorted(costo_por_activo.items(), key=lambda kv: -kv[1])[:8]],
    }
