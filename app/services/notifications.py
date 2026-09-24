"""Avisos internos (E-12): contratos por vencer, documentos, caducidades, existencias, mantenimientos
y tareas vencidas.

Diseño:
- `generate()` recorre las reglas y crea avisos. Es idempotente: `dedupe_key` incluye el periodo
  (semana o día), así que correrlo varias veces no duplica.
- Se puede **silenciar** un aviso recurrente (`mute_key`), como pidió el cliente.
- El correo NO se envía desde aquí: se marca `sin_adaptador` mientras no se configure el envío
  (regla 3 del proyecto). Cuando exista adaptador, este es el único punto a tocar.
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import config
from app.audit import record
from app.models import (Asset, Attachment, EmploymentContract, Lot, MaintenancePlan, Notification,
                        NotificationMute, Product, Task, User, utcnow)
from app.permissions import has_permission
from app.services.business_time import to_local
from app.services.common import DomainError, get_or_404

KIND_LABELS = {
    "contrato_por_vencer": "Contrato por vencer", "documento_por_vencer": "Documento por vencer",
    "lote_por_caducar": "Lote por caducar", "existencia_baja": "Existencia bajo el mínimo",
    "mantenimiento_programado": "Mantenimiento programado", "tarea_vencida": "Tarea vencida",
}


def _week(dt=None) -> str:
    y, w, _ = to_local(dt or utcnow()).isocalendar()
    return f"{y}-W{w:02d}"


def _day(dt=None) -> str:
    return to_local(dt or utcnow()).date().isoformat()


def is_muted(db: Session, mute_key: str) -> bool:
    m = db.get(NotificationMute, mute_key)
    return bool(m and (m.until is None or m.until > utcnow()))


def push(db: Session, *, kind: str, title: str, dedupe_key: str, mute_key: str, body: str | None = None,
         severity: str = "info", entity_type: str | None = None, entity_id: str | None = None,
         link: str | None = None, target_role: str | None = None, target_user_id: str | None = None,
         due_on=None) -> Notification | None:
    """Crea el aviso si no existe ya para este periodo y no está silenciado."""
    if is_muted(db, mute_key):
        return None
    if db.scalar(select(Notification).where(Notification.dedupe_key == dedupe_key)):
        return None
    n = Notification(kind=kind, title=title[:200], body=body, severity=severity, entity_type=entity_type,
                     entity_id=entity_id, link=link, target_role=target_role, target_user_id=target_user_id,
                     due_on=due_on, dedupe_key=dedupe_key[:200], mute_key=mute_key[:160],
                     email_status="pendiente" if config.NOTIFY_EMAIL_ENABLED else "sin_adaptador")
    db.add(n)
    db.flush()
    return n


def _days_left(when) -> int:
    return (to_local(when).date() - to_local(utcnow()).date()).days


def _sev(days: int) -> str:
    return "bad" if days < 0 else "warn"


def generate(db: Session, actor_id: str | None = None) -> dict:
    """Ejecuta todas las reglas. Programable una vez al día (ver README)."""
    now = utcnow()
    created: dict[str, int] = {k: 0 for k in KIND_LABELS}

    def add(**kw) -> None:
        if push(db, **kw):
            created[kw["kind"]] += 1

    # 1) Contratos: aviso SEMANAL desde 2 meses antes del vencimiento (E-08)
    limit = now + timedelta(days=config.CONTRACT_ALERT_DAYS)
    for c in db.scalars(select(EmploymentContract).where(EmploymentContract.status == "vigente",
                                                         EmploymentContract.end_on.is_not(None),
                                                         EmploymentContract.end_on <= limit)):
        d = _days_left(c.end_on)
        add(kind="contrato_por_vencer", severity=_sev(d), entity_type="employee", entity_id=c.employee_id,
            link=f"/rrhh/empleados/{c.employee_id}", target_role="rrhh", due_on=c.end_on,
            title=f"Contrato de {c.employee.full_name} {'vencido' if d < 0 else f'vence en {d} días'}",
            body=f"Contrato {c.type} con fin el {to_local(c.end_on).date().isoformat()}.",
            dedupe_key=f"contrato:{c.id}:{_week()}", mute_key=f"contrato:{c.id}")

    # 2) Documentos adjuntos con vencimiento (pólizas de garantía, seguros, verificaciones…)
    doc_limit = now + timedelta(days=config.DOC_EXPIRY_ALERT_DAYS)
    role_by_entity = {"asset": "mantenimiento", "employee": "rrhh", "petty_cash": "administracion"}
    for a in db.scalars(select(Attachment).where(Attachment.expires_on.is_not(None),
                                                 Attachment.expires_on <= doc_limit)):
        d = _days_left(a.expires_on)
        link = {"asset": f"/mantenimiento/activos/{a.entity_id}",
                "employee": f"/rrhh/empleados/{a.entity_id}"}.get(a.entity_type)
        add(kind="documento_por_vencer", severity=_sev(d), entity_type=a.entity_type, entity_id=a.entity_id,
            link=link, target_role=role_by_entity.get(a.entity_type, "administracion"), due_on=a.expires_on,
            title=f"{a.title} {'venció' if d < 0 else f'vence en {d} días'}",
            body=f"Documento «{a.title}» ({a.kind}).",
            dedupe_key=f"doc:{a.id}:{_week()}", mute_key=f"doc:{a.id}")

    # 3) Lotes por caducar (rastreo FSSC 22000)
    lot_limit = now + timedelta(days=config.LOT_EXPIRY_ALERT_DAYS)
    from app.services import inventory as inv
    for lot in db.scalars(select(Lot).where(Lot.expires_on.is_not(None), Lot.expires_on <= lot_limit)):
        kg = inv.lot_balance(db, lot.id)
        if kg <= 0:
            continue
        d = _days_left(lot.expires_on)
        add(kind="lote_por_caducar", severity=_sev(d), entity_type="lot", entity_id=lot.id,
            link="/inventario/lotes", target_role="almacen", due_on=lot.expires_on,
            title=f"Lote {lot.code} de {lot.product.name} {'caducó' if d < 0 else f'caduca en {d} días'}",
            body=f"Quedan {kg:g} kg en existencia.",
            dedupe_key=f"lote:{lot.id}:{_week()}", mute_key=f"lote:{lot.id}")

    # 4) Existencias bajo el mínimo (diario)
    for row in inv.low_stock(db):
        add(kind="existencia_baja", severity="warn", entity_type="product", entity_id=row["product"].id,
            link="/inventario", target_role="almacen",
            title=f"{row['product'].name}: {row['kg']:g} kg (mínimo {row['min_kg']:g} kg)",
            body="Existencia por debajo del mínimo configurado.",
            dedupe_key=f"minimo:{row['product'].id}:{_day()}", mute_key=f"minimo:{row['product'].id}")

    # 5) Mantenimientos programados (por fecha, kilómetros u horas; vence lo que ocurra primero)
    for plan in db.scalars(select(MaintenancePlan).where(MaintenancePlan.is_active.is_(True))):
        asset = plan.asset
        reasons, sev, days = [], "warn", None
        if plan.next_due_on:
            days = _days_left(plan.next_due_on)
            if days <= config.MAINT_ALERT_DAYS:
                reasons.append("vencido por fecha" if days < 0 else f"vence en {days} días")
                sev = _sev(days)
        if plan.next_due_km and asset.odometer_km is not None:
            falta = plan.next_due_km - asset.odometer_km
            if falta <= config.MAINT_ALERT_KM:
                reasons.append("vencido por kilometraje" if falta < 0 else f"faltan {falta:g} km")
                sev = "bad" if falta < 0 else sev
        if plan.next_due_hours and asset.hours_used is not None:
            falta = plan.next_due_hours - asset.hours_used
            if falta <= config.MAINT_ALERT_HOURS:
                reasons.append("vencido por horas" if falta < 0 else f"faltan {falta:g} h")
                sev = "bad" if falta < 0 else sev
        if not reasons:
            continue
        add(kind="mantenimiento_programado", severity=sev, entity_type="asset", entity_id=asset.id,
            link=f"/mantenimiento/activos/{asset.id}", target_role="mantenimiento",
            target_user_id=plan.assignee_user_id, due_on=plan.next_due_on,
            title=f"{asset.name}: {plan.name} ({', '.join(reasons)})",
            body=f"Activo {asset.code}. Plan «{plan.name}».",
            dedupe_key=f"plan:{plan.id}:{_week()}", mute_key=f"plan:{plan.id}")

    # 6) Tareas vencidas (diario)
    for t in db.scalars(select(Task).where(Task.status == "pendiente", Task.due_at.is_not(None), Task.due_at < now)):
        add(kind="tarea_vencida", severity="bad", entity_type="task", entity_id=t.id, link="/tasks",
            target_role=t.assignee_role, target_user_id=t.assignee_id, due_on=t.due_at,
            title=f"Tarea vencida: {t.title}", body=f"Vencía el {to_local(t.due_at).strftime('%d/%m/%Y %H:%M')}.",
            dedupe_key=f"tarea:{t.id}:{_day()}", mute_key=f"tarea:{t.id}")

    total = sum(created.values())
    if total:
        record(db, actor_id, "aviso.generado", "notification", None, after=created, category="sistema",
               summary=f"{total} avisos nuevos")
    db.commit()
    return {"created": created, "total": total}


def _visible(stmt, user: User):
    """Un administrador ve todos los avisos; los demás, los de su área o los suyos."""
    if has_permission(user.role, "audit:read"):
        return stmt
    return stmt.where((Notification.target_role == user.role) | (Notification.target_user_id == user.id)
                      | (Notification.target_role.is_(None) & Notification.target_user_id.is_(None)))


def listing(db: Session, user: User, status: str | None = "pendiente", kind: str | None = None) -> list[Notification]:
    stmt = select(Notification)
    if status:
        stmt = stmt.where(Notification.status == status)
    if kind:
        stmt = stmt.where(Notification.kind == kind)
    return list(db.scalars(_visible(stmt, user).order_by(Notification.created_at.desc()).limit(300)))


def pending_count(db: Session, user: User) -> int:
    stmt = select(func.count()).select_from(Notification).where(Notification.status == "pendiente")
    return db.scalar(_visible(stmt, user)) or 0


def mark_read(db: Session, notification_id: str, actor_id: str) -> Notification:
    n = get_or_404(db, Notification, notification_id, "Aviso")
    n.status, n.read_at, n.read_by = "leida", utcnow(), actor_id
    record(db, actor_id, "aviso.leido", "notification", n.id, after={"titulo": n.title},
           summary=f"Aviso marcado como leído: {n.title}")
    db.commit()
    return n


def mute(db: Session, mute_key: str, days: int | None, actor_id: str, reason: str | None = None) -> NotificationMute:
    """Silencia un aviso recurrente. `days=None` lo silencia sin fecha de término."""
    if not mute_key:
        raise DomainError("Falta el aviso a silenciar")
    until = utcnow() + timedelta(days=int(days)) if days else None
    m = db.get(NotificationMute, mute_key) or NotificationMute(mute_key=mute_key)
    m.until, m.muted_by, m.at, m.reason = until, actor_id, utcnow(), (reason or None)
    db.add(m)
    for n in db.scalars(select(Notification).where(Notification.mute_key == mute_key,
                                                   Notification.status == "pendiente")):
        n.status, n.read_at, n.read_by = "leida", utcnow(), actor_id
    record(db, actor_id, "aviso.silenciado", "notification", None,
           after={"mute_key": mute_key, "hasta": until.isoformat() if until else "sin fecha", "motivo": reason},
           category="sistema", summary=f"Avisos silenciados: {mute_key}")
    db.commit()
    return m


def unmute(db: Session, mute_key: str, actor_id: str) -> None:
    m = db.get(NotificationMute, mute_key)
    if m:
        db.delete(m)
        record(db, actor_id, "aviso.reactivado", "notification", None, after={"mute_key": mute_key},
               category="sistema", summary=f"Avisos reactivados: {mute_key}")
        db.commit()


def metrics(db: Session) -> dict:
    rows = dict(db.execute(select(Notification.kind, func.count()).where(Notification.status == "pendiente")
                           .group_by(Notification.kind)).all())
    return {"pendientes": sum(rows.values()), "por_tipo": {KIND_LABELS.get(k, k): v for k, v in rows.items()},
            "silenciados": db.scalar(select(func.count()).select_from(NotificationMute)) or 0}
