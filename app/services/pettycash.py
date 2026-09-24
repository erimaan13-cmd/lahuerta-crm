"""Caja chica de fondo fijo (E-09).

Cómo funciona el fondo fijo: la caja arranca con un monto asignado, cada gasto lo baja y cada
reposición lo devuelve a su nivel. Por eso el saldo se calcula así:

    saldo = monto del fondo + reposiciones − gastos

Reglas que el cliente pidió explícitamente:
- El **comprobante es obligatorio** en cada gasto: sin comprobante no hay gasto (por eso la ruta sube
  el archivo primero y aquí solo se acepta el `receipt_id` ya guardado).
- El administrador asigna quién maneja cada caja (`responsible_user_id`).
- Exportación periódica en CSV para el contador.

Un gasto nunca puede dejar la caja en negativo: si eso ocurriera, el saldo dejaría de servir para
saber cuánto efectivo debe haber físicamente en la caja.
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record
from app.models import Attachment, PettyCashEntry, PettyCashFund, User, utcnow
from app.services.business_time import to_local, to_utc_naive
from app.services.common import DomainError, get_or_404
from app.services.files import parse_date
from app.services.inventory import num

CATEGORIES = {
    "papeleria": "Papelería", "limpieza": "Limpieza", "combustible": "Combustible",
    "mensajeria": "Mensajería y envíos", "alimentos": "Alimentos", "herramienta": "Herramienta menor",
    "mantenimiento": "Mantenimiento menor", "viaticos": "Viáticos", "servicios": "Servicios",
    "otro": "Otro",
}
TYPES = {"gasto": "Gasto", "reposicion": "Reposición"}


# ------------------------------------------------------------------ cajas
def create_fund(db: Session, data: dict, actor_id: str | None) -> PettyCashFund:
    name = (data.get("name") or "").strip()
    if not name:
        raise DomainError("La caja necesita un nombre")
    if db.scalar(select(PettyCashFund).where(PettyCashFund.name == name)):
        raise DomainError(f"Ya existe una caja llamada «{name}»")
    monto = num(data.get("fund_amount_mxn"), "el monto del fondo", minimum=0.01)
    responsable = data.get("responsible_user_id") or None
    if responsable:
        get_or_404(db, User, responsable, "Usuario responsable")
    f = PettyCashFund(name=name[:120], fund_amount_mxn=round(monto, 2), responsible_user_id=responsable)
    db.add(f)
    db.flush()
    record(db, actor_id, "caja.alta", "petty_cash", f.id,
           after={"caja": f.name, "fondo_mxn": f.fund_amount_mxn, "responsable": responsable},
           summary=f"Caja chica creada: {f.name} (${f.fund_amount_mxn:,.2f})")
    db.commit()
    return f


def update_fund(db: Session, fund_id: str, data: dict, actor_id: str | None) -> PettyCashFund:
    f = get_or_404(db, PettyCashFund, fund_id, "Caja chica")
    before = {"fondo_mxn": f.fund_amount_mxn, "responsable": f.responsible_user_id, "activa": f.is_active}
    if data.get("fund_amount_mxn") not in (None, ""):
        f.fund_amount_mxn = round(num(data["fund_amount_mxn"], "el monto del fondo", minimum=0.01), 2)
    if "responsible_user_id" in data:
        if data.get("responsible_user_id"):
            get_or_404(db, User, data["responsible_user_id"], "Usuario responsable")
        f.responsible_user_id = data.get("responsible_user_id") or None
    if "is_active" in data:
        f.is_active = str(data.get("is_active")) in ("1", "True", "true", "on")
    record(db, actor_id, "caja.cambio", "petty_cash", f.id, before=before,
           after={"fondo_mxn": f.fund_amount_mxn, "responsable": f.responsible_user_id, "activa": f.is_active},
           summary=f"Caja actualizada: {f.name}")
    db.commit()
    return f


def funds(db: Session, only_active: bool = False) -> list[PettyCashFund]:
    stmt = select(PettyCashFund).order_by(PettyCashFund.name)
    if only_active:
        stmt = stmt.where(PettyCashFund.is_active.is_(True))
    return list(db.scalars(stmt))


# ------------------------------------------------------------------ saldo y movimientos
def _monto(data: dict) -> float:
    """Lee el monto del formulario o del JSON. Un 0 es un valor dado, no un campo vacío."""
    raw = data.get("amount_mxn")
    if raw in (None, ""):
        raw = data.get("amount")
    return round(num(raw, "el monto"), 2)


def _sum(db: Session, fund_id: str, type_: str) -> float:
    return float(db.scalar(select(func.coalesce(func.sum(PettyCashEntry.amount_mxn), 0.0))
                           .where(PettyCashEntry.fund_id == fund_id, PettyCashEntry.type == type_)) or 0.0)


def balance(db: Session, fund_id: str) -> float:
    """Fondo + reposiciones − gastos: lo que debe haber en efectivo dentro de la caja."""
    f = get_or_404(db, PettyCashFund, fund_id, "Caja chica")
    return round(f.fund_amount_mxn + _sum(db, f.id, "reposicion") - _sum(db, f.id, "gasto"), 2)


def entries(db: Session, fund_id: str, desde=None, hasta=None) -> list[PettyCashEntry]:
    stmt = select(PettyCashEntry).where(PettyCashEntry.fund_id == fund_id)
    d, h = parse_date(desde), parse_date(hasta)
    if d:
        stmt = stmt.where(PettyCashEntry.at >= d)
    if h:
        stmt = stmt.where(PettyCashEntry.at < h + timedelta(days=1))  # el día "hasta" se incluye completo
    return list(db.scalars(stmt.order_by(PettyCashEntry.at.desc())))


def _add_entry(db: Session, fund: PettyCashFund, *, type_: str, data: dict, receipt_id: str | None,
               actor_id: str | None) -> PettyCashEntry:
    monto = _monto(data)
    if monto <= 0:
        raise DomainError("El monto debe ser mayor que cero")
    descripcion = (data.get("description") or "").strip()
    if not descripcion:
        raise DomainError("Escribe para qué fue el movimiento")
    if receipt_id:
        att = get_or_404(db, Attachment, receipt_id, "Comprobante")
        if att.entity_type != "petty_cash" or att.entity_id != fund.id:
            raise DomainError("El comprobante no pertenece a esta caja")
    at = parse_date(data.get("at")) or utcnow()
    categoria = (data.get("category") or "otro") if type_ == "gasto" else None
    if type_ == "gasto" and categoria not in CATEGORIES:
        raise DomainError(f"Categoría no válida: {categoria}")
    e = PettyCashEntry(fund_id=fund.id, at=at, type=type_, category=categoria, amount_mxn=monto,
                       description=descripcion[:300], receipt_id=receipt_id, actor_id=actor_id)
    db.add(e)
    db.flush()
    record(db, actor_id, f"caja.{type_}", "petty_cash", fund.id,
           after={"movimiento_id": e.id, "fecha": to_local(at).date().isoformat(), "tipo": type_,
                  "categoria": categoria, "monto_mxn": monto, "descripcion": e.description,
                  "comprobante": bool(receipt_id), "saldo_resultante": balance(db, fund.id)},
           summary=f"{TYPES[type_]} de ${monto:,.2f} en {fund.name}: {e.description[:80]}")
    db.commit()
    return e


def add_expense(db: Session, fund_id: str, data: dict, actor_id: str | None,
                receipt_id: str | None = None) -> PettyCashEntry:
    """Gasto de la caja. Sin comprobante no se registra (E-09) y nunca deja la caja en negativo."""
    fund = get_or_404(db, PettyCashFund, fund_id, "Caja chica")
    if not fund.is_active:
        raise DomainError(f"La caja «{fund.name}» está cerrada")
    receipt_id = receipt_id or data.get("receipt_id") or None
    if not receipt_id:
        raise DomainError("El gasto necesita comprobante: adjunta el ticket o la factura")
    monto = _monto(data)
    if monto <= 0:
        raise DomainError("El monto debe ser mayor que cero")
    saldo = balance(db, fund.id)
    if monto > saldo + 1e-6:
        raise DomainError(f"El gasto de ${monto:,.2f} deja la caja «{fund.name}» en negativo: "
                          f"el saldo disponible es ${saldo:,.2f}. Registra primero una reposición.")
    return _add_entry(db, fund, type_="gasto", data=data, receipt_id=receipt_id, actor_id=actor_id)


def add_replenishment(db: Session, fund_id: str, data: dict, actor_id: str | None,
                      receipt_id: str | None = None) -> PettyCashEntry:
    """Reposición del fondo fijo: devuelve a la caja el efectivo ya comprobado."""
    fund = get_or_404(db, PettyCashFund, fund_id, "Caja chica")
    if not fund.is_active:
        raise DomainError(f"La caja «{fund.name}» está cerrada")
    data = {**data, "description": (data.get("description") or "").strip() or "Reposición del fondo"}
    return _add_entry(db, fund, type_="reposicion", data=data,
                      receipt_id=receipt_id or data.get("receipt_id") or None, actor_id=actor_id)


# ------------------------------------------------------------------ tablero y exportación
def _month_start():
    """Primer día del mes en hora de Monterrey, convertido a UTC (así se guardan las fechas)."""
    hoy = to_local(utcnow())
    return to_utc_naive(hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0))


def metrics(db: Session) -> dict:
    cajas = funds(db)
    saldos = {f.name: balance(db, f.id) for f in cajas}
    desde = _month_start()
    por_categoria = dict(db.execute(select(PettyCashEntry.category, func.sum(PettyCashEntry.amount_mxn))
                                    .where(PettyCashEntry.type == "gasto", PettyCashEntry.at >= desde)
                                    .group_by(PettyCashEntry.category)).all())
    gasto_mes = round(sum(float(v or 0) for v in por_categoria.values()), 2)
    total = float(db.scalar(select(func.coalesce(func.sum(PettyCashEntry.amount_mxn), 0.0))
                            .where(PettyCashEntry.type == "gasto")) or 0.0)
    return {"cajas_activas": sum(1 for f in cajas if f.is_active), "saldo_por_caja": saldos,
            "saldo_total": round(sum(saldos.values()), 2), "gasto_mes_mxn": gasto_mes,
            "gasto_total_mxn": round(total, 2),
            "gasto_mes_por_categoria": {CATEGORIES.get(k, k or "Otro"): round(float(v or 0), 2)
                                        for k, v in sorted(por_categoria.items(),
                                                           key=lambda kv: -(kv[1] or 0))}}


def export_rows(db: Session, fund_id: str, desde=None, hasta=None) -> list[list]:
    """Filas listas para el contador: encabezado + movimientos del periodo."""
    fund = get_or_404(db, PettyCashFund, fund_id, "Caja chica")
    rows = [["fecha", "caja", "tipo", "categoria", "monto_mxn", "descripcion", "responsable", "comprobante"]]
    for e in sorted(entries(db, fund.id, desde, hasta), key=lambda x: x.at):
        actor = db.get(User, e.actor_id) if e.actor_id else None
        rows.append([to_local(e.at).strftime("%Y-%m-%d"), fund.name, TYPES.get(e.type, e.type),
                     CATEGORIES.get(e.category, "") if e.category else "", f"{e.amount_mxn:.2f}",
                     e.description, actor.full_name if actor else "", "sí" if e.receipt_id else "no"])
    return rows


def export_csv(db: Session, fund_id: str, desde=None, hasta=None) -> str:
    """Devuelve el CSV como texto (la ruta solo le pone los encabezados HTTP)."""
    import csv
    import io
    buf = io.StringIO()
    csv.writer(buf).writerows(export_rows(db, fund_id, desde, hasta))
    return buf.getvalue()
