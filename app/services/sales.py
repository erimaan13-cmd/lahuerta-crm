"""Ventas: pedidos que descuentan inventario al entregarse (E-06, D-33).

Decisiones que implementa:
- El pedido es una entidad real del sistema (D-33). `OrderReference` sigue siendo solo el espejo de
  lo que ya existe en el ERP; `SalesOrder` es el pedido que la empresa captura y surte aquí.
- El sistema NO factura. La factura se emite por fuera (CONTPAQi) y aquí solo se captura su folio,
  para amarrar pedido y factura sin duplicar el proceso contable.
- Confirmar solo VERIFICA existencia; entregar es lo único que descuenta. Así un pedido confirmado
  no "aparta" kilos de forma invisible: la existencia sigue siendo la suma de los movimientos.
- Si el renglón no indica lote, al entregar se surte por PEPS de caducidad: sale primero el lote que
  caduca antes. En alimentos esa es la regla correcta, y evita quedarse con lote viejo en bodega.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record, snapshot
from app.models import (Account, Contact, Lot, Product, SalesOrder, SalesOrderItem, StockMovement,
                        Warehouse, utcnow)
from app.services import inventory
from app.services.business_time import to_local
from app.services.common import DomainError, get_or_404
from app.services.files import parse_date

STATUS_LABELS = {"borrador": "Borrador", "confirmado": "Confirmado", "entregado": "Entregado",
                 "cancelado": "Cancelado"}
# Transiciones válidas: un pedido entregado o cancelado ya no se mueve (el historial no se reescribe).
TRANSITIONS = {"borrador": {"confirmado", "cancelado"}, "confirmado": {"entregado", "cancelado"},
               "entregado": set(), "cancelado": set()}
MAX_ITEMS_UI = 5  # renglones que ofrece el formulario de alta
_FAR = datetime(9999, 12, 31)  # un lote sin caducidad capturada se surte al final


def _clean(v):
    return v.strip() if isinstance(v, str) and v.strip() else (None if isinstance(v, str) else v)


# ------------------------------------------------------------------ alta
def _item_kg(db: Session, product: Product, raw: dict) -> float:
    """Kilos del renglón: se aceptan kilos directos o unidades de manejo (sacos, cajas) convertidas."""
    if raw.get("qty_kg") not in (None, ""):
        kg = inventory.num(raw.get("qty_kg"), "la cantidad en kilos", minimum=0.001)
    else:
        unit = raw.get("unit") or product.unit or "kg"
        if unit not in inventory.UNITS:
            raise DomainError(f"Unidad no válida: {unit}")
        kg = inventory.to_kg(product, inventory.num(raw.get("qty"), "la cantidad", minimum=0.001), unit)
    if kg <= 0:
        raise DomainError("La cantidad del renglón debe ser mayor que cero")
    return round(kg, 3)


def create_order(db: Session, data: dict, items: list[dict], actor_id: str | None) -> SalesOrder:
    """Alta de pedido en borrador. Cuenta, bodega y al menos un renglón son obligatorios."""
    account = get_or_404(db, Account, data.get("account_id") or "", "Cuenta")
    warehouse = get_or_404(db, Warehouse, data.get("warehouse_id") or "", "Bodega")
    if data.get("contact_id"):
        get_or_404(db, Contact, data["contact_id"], "Contacto")
    if not items:
        raise DomainError("El pedido necesita al menos un renglón")
    promised = parse_date(data.get("promised_date"))
    if promised is None:
        raise DomainError("La fecha prometida de entrega es obligatoria")
    n = db.scalar(select(func.count()).select_from(SalesOrder)) + 1
    order = SalesOrder(folio=f"PED-{n:04d}", account_id=account.id, contact_id=data.get("contact_id") or None,
                       opportunity_id=data.get("opportunity_id") or None, warehouse_id=warehouse.id,
                       promised_date=promised, notes=_clean(data.get("notes")),
                       owner_id=data.get("owner_id") or actor_id, is_demo=bool(data.get("is_demo", False)))
    for raw in items:
        product = get_or_404(db, Product, raw.get("product_id") or "", "Producto")
        lot = get_or_404(db, Lot, raw["lot_id"], "Lote") if raw.get("lot_id") else None
        if lot and lot.product_id != product.id:
            raise DomainError(f"El lote {lot.code} no pertenece a {product.name}")
        price = inventory.num(raw.get("unit_price_mxn"), "el precio por kilo", required=False, minimum=0)
        order.items.append(SalesOrderItem(product_id=product.id, lot_id=lot.id if lot else None,
                                          qty_kg=_item_kg(db, product, raw), unit_price_mxn=price,
                                          packaging=raw.get("packaging") or product.packaging))
    db.add(order)
    db.flush()
    record(db, actor_id, "pedido.alta", "sales_order", order.id,
           after={"folio": order.folio, "cuenta": account.name, "bodega": warehouse.code,
                  "kg": order.total_kg, "total_mxn": order.total_mxn, "renglones": len(order.items)},
           summary=f"Pedido {order.folio} creado para {account.name} ({order.total_kg:g} kg)")
    db.commit()
    return order


# ------------------------------------------------------------------ existencia y surtido
def _require(order: SalesOrder, new_status: str) -> None:
    if new_status not in TRANSITIONS.get(order.status, set()):
        raise DomainError(f"El pedido {order.folio} está {STATUS_LABELS.get(order.status, order.status).lower()}: "
                          f"no se puede pasar a {STATUS_LABELS.get(new_status, new_status).lower()}")


def check_stock(db: Session, order: SalesOrder) -> None:
    """Verifica que la bodega del pedido cubra cada renglón, SIN descontar nada."""
    if not order.warehouse_id:
        raise DomainError("El pedido no tiene bodega asignada")
    por_lote: dict[tuple[str, str], float] = {}
    por_producto: dict[str, float] = {}
    for it in order.items:
        por_producto[it.product_id] = round(por_producto.get(it.product_id, 0.0) + it.qty_kg, 3)
        if it.lot_id:
            k = (it.product_id, it.lot_id)
            por_lote[k] = round(por_lote.get(k, 0.0) + it.qty_kg, 3)
    faltantes = []
    for (pid, lid), kg in por_lote.items():
        disponible = inventory.balance(db, pid, order.warehouse_id, lid)
        if disponible + 1e-6 < kg:
            lot = db.get(Lot, lid)
            faltantes.append(f"{db.get(Product, pid).name} lote {lot.code}: hay {disponible:g} kg, se piden {kg:g} kg")
    for pid, kg in por_producto.items():
        disponible = inventory.balance(db, pid, order.warehouse_id)
        if disponible + 1e-6 < kg:
            faltantes.append(f"{db.get(Product, pid).name}: hay {disponible:g} kg, se piden {kg:g} kg")
    if faltantes:
        raise DomainError("No hay existencia suficiente en la bodega del pedido — " + "; ".join(faltantes))


def plan_item(db: Session, item: SalesOrderItem, warehouse_id: str) -> list[tuple[str | None, float]]:
    """Reparte un renglón entre lotes: PEPS por caducidad. Devuelve [(lot_id, kg)]."""
    qty = round(item.qty_kg, 3)
    if item.lot_id:
        return [(item.lot_id, qty)]
    rows = [r for r in inventory.stock_rows(db, item.product_id, warehouse_id) if r["kg"] > 1e-6]
    con_lote = sorted([r for r in rows if r["lot"]],
                      key=lambda r: (r["lot"].expires_on or _FAR, r["lot"].code))
    sin_lote = [r for r in rows if not r["lot"]]  # existencia sin lote: se surte al final
    reparto, restante = [], qty
    for r in con_lote + sin_lote:
        if restante <= 1e-6:
            break
        toma = round(min(r["kg"], restante), 3)
        reparto.append((r["lot"].id if r["lot"] else None, toma))
        restante = round(restante - toma, 3)
    if restante > 1e-6:
        product = db.get(Product, item.product_id)
        raise DomainError(f"No hay existencia suficiente de {product.name}: faltan {restante:g} kg")
    return reparto


# ------------------------------------------------------------------ estados
def confirm(db: Session, order_id: str, actor_id: str | None) -> SalesOrder:
    """Confirma el pedido tras verificar existencia. No descuenta: eso ocurre al entregar."""
    order = get_or_404(db, SalesOrder, order_id, "Pedido")
    _require(order, "confirmado")
    check_stock(db, order)
    before = snapshot(order)
    order.status = "confirmado"
    record(db, actor_id, "pedido.confirmado", "sales_order", order.id, before, snapshot(order),
           summary=f"Pedido {order.folio} confirmado ({order.total_kg:g} kg)")
    db.commit()
    return order


def deliver(db: Session, order_id: str, actor_id: str | None) -> SalesOrder:
    """Entrega: descuenta inventario renglón por renglón y deja cada salida ligada al pedido."""
    order = get_or_404(db, SalesOrder, order_id, "Pedido")
    _require(order, "entregado")
    check_stock(db, order)  # falla antes de tocar el inventario
    try:
        surtido = []
        for it in order.items:
            for lot_id, kg in plan_item(db, it, order.warehouse_id):
                inventory.move(db, type="salida", product_id=it.product_id, warehouse_id=order.warehouse_id,
                               qty_kg=-kg, lot_id=lot_id, actor_id=actor_id, ref_type="pedido", ref_id=order.id,
                               reason=f"Entrega del pedido {order.folio}", commit=False)
                lot = db.get(Lot, lot_id) if lot_id else None
                surtido.append({"producto": db.get(Product, it.product_id).name,
                                "lote": lot.code if lot else "sin lote", "kg": kg})
        before = snapshot(order)
        order.status, order.delivered_at = "entregado", utcnow()
        # Quien ya recibió mercancía dejó de ser prospecto (mantiene coherente el ciclo de vida de la cuenta).
        if order.account.lifecycle == "prospecto":
            order.account.lifecycle = "cliente_activo"
        record(db, actor_id, "pedido.entregado", "sales_order", order.id, before,
               {**snapshot(order), "surtido": surtido},
               summary=f"Pedido {order.folio} entregado ({order.total_kg:g} kg descontados de inventario)")
        db.commit()
    except Exception:
        db.rollback()  # o se descuenta todo el pedido o no se descuenta nada
        raise
    return order


def cancel(db: Session, order_id: str, actor_id: str | None, motivo: str | None) -> SalesOrder:
    """Cancela un pedido antes de entregarlo. Lo entregado ya movió inventario: se corrige con un ajuste."""
    order = get_or_404(db, SalesOrder, order_id, "Pedido")
    _require(order, "cancelado")
    motivo = _clean(motivo)
    if not motivo:
        raise DomainError("Para cancelar un pedido indica el motivo")
    before = snapshot(order)
    order.status = "cancelado"
    order.notes = f"{order.notes + chr(10) if order.notes else ''}Cancelado: {motivo}"
    record(db, actor_id, "pedido.cancelado", "sales_order", order.id, before, snapshot(order),
           summary=f"Pedido {order.folio} cancelado: {motivo}")
    db.commit()
    return order


def set_invoice(db: Session, order_id: str, folio: str | None, actor_id: str | None) -> SalesOrder:
    """Captura manual del folio de la factura emitida por fuera (CONTPAQi). El sistema no factura."""
    order = get_or_404(db, SalesOrder, order_id, "Pedido")
    folio = _clean(folio)
    if not folio:
        raise DomainError("Captura el folio de la factura")
    if order.status == "cancelado":
        raise DomainError("Un pedido cancelado no lleva factura")
    if order.status == "borrador":
        raise DomainError("Confirma el pedido antes de capturar la factura")
    before = snapshot(order)
    order.invoice_folio = folio[:40]
    record(db, actor_id, "pedido.factura", "sales_order", order.id, before, snapshot(order),
           summary=f"Factura {order.invoice_folio} capturada en el pedido {order.folio}")
    db.commit()
    return order


# ------------------------------------------------------------------ consultas
def listing(db: Session, status: str | None = None, account_id: str | None = None) -> list[SalesOrder]:
    stmt = select(SalesOrder).order_by(SalesOrder.created_at.desc())
    if status:
        stmt = stmt.where(SalesOrder.status == status)
    if account_id:
        stmt = stmt.where(SalesOrder.account_id == account_id)
    return list(db.scalars(stmt))


def for_account(db: Session, account_id: str) -> list[SalesOrder]:
    return listing(db, account_id=account_id)


def movements_of(db: Session, order_id: str) -> list[StockMovement]:
    """Movimientos de inventario que generó la entrega de este pedido."""
    return list(db.scalars(select(StockMovement).where(StockMovement.ref_type == "pedido",
                                                       StockMovement.ref_id == order_id)
                           .order_by(StockMovement.at)))


def _months(n: int = 6) -> list[str]:
    primero = to_local(utcnow()).date().replace(day=1)
    out = []
    for _ in range(n):
        out.append(primero.strftime("%Y-%m"))
        primero = (primero - timedelta(days=1)).replace(day=1)
    return list(reversed(out))


def metrics(db: Session) -> dict:
    """Kilos y pesos por mes, top clientes y productos, pedidos por estado y pendientes de entrega."""
    meses = {m: {"kg": 0.0, "mxn": 0.0, "pedidos": 0} for m in _months()}
    por_estado = {k: 0 for k in STATUS_LABELS}
    por_cuenta: dict[str, float] = {}
    por_producto: dict[str, float] = {}
    kg_total = mxn_total = 0.0
    for o in db.scalars(select(SalesOrder)):
        por_estado[o.status] = por_estado.get(o.status, 0) + 1
        if o.status == "cancelado":
            continue
        kg_total += o.total_kg
        mxn_total += o.total_mxn
        # Un pedido sin entregar se cuenta en el mes en que se capturó: así el mes en curso no sale vacío.
        mes = to_local(o.delivered_at or o.created_at).strftime("%Y-%m")
        if mes in meses:
            meses[mes]["kg"] = round(meses[mes]["kg"] + o.total_kg, 2)
            meses[mes]["mxn"] = round(meses[mes]["mxn"] + o.total_mxn, 2)
            meses[mes]["pedidos"] += 1
        por_cuenta[o.account.name] = round(por_cuenta.get(o.account.name, 0.0) + o.total_kg, 2)
        for it in o.items:
            nombre = it.product.name
            por_producto[nombre] = round(por_producto.get(nombre, 0.0) + it.qty_kg, 2)
    pendientes = sorted([o for o in db.scalars(select(SalesOrder).where(SalesOrder.status == "confirmado"))],
                        key=lambda o: (o.promised_date or _FAR))
    return {
        "kg_total": round(kg_total, 2), "mxn_total": round(mxn_total, 2),
        "por_mes": [{"mes": m, **v} for m, v in meses.items()],
        "por_estado": por_estado,
        "top_clientes": [{"nombre": k, "kg": v} for k, v in
                         sorted(por_cuenta.items(), key=lambda kv: -kv[1])[:8]],
        "top_productos": [{"nombre": k, "kg": v} for k, v in
                          sorted(por_producto.items(), key=lambda kv: -kv[1])[:8]],
        "pendientes_de_entrega": len(pendientes),
        "pendientes": pendientes[:10],
    }
