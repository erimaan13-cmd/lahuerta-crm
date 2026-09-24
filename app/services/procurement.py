"""Abastecimiento: proveedores y órdenes de compra.

Decisiones que implementa (AT-15):
- E-03 el proveedor es entidad real (antes solo servía para enrutar correos).
- E-07 la autorización depende del monto: con 7–15 empleados una cadena larga de firmas solo detiene
  la operación, así que solo las órdenes arriba de `config.PO_AUTH_THRESHOLD_MXN` piden autorización.
- E-04 lote y caducidad se capturan a mano al recibir; la recepción es la que da de alta el lote.

La cantidad y el costo de una orden SIEMPRE van en kilos (`qty_kg`, `unit_cost_mxn`), porque el precio
se negocia por kilo. La captura en sacos o cajas vive en el módulo de inventario, no aquí.

La recepción no toca ninguna columna de existencias: registra una ENTRADA de inventario con
`ref_type="orden_compra"`, de modo que cada kilo en bodega se puede rastrear hasta su orden.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import config
from app.audit import record
from app.models import (Lot, Product, PurchaseOrder, PurchaseOrderItem, Supplier, Warehouse, utcnow)
from app.services import inventory
from app.services.common import DomainError, get_or_404, norm_email, norm_phone
from app.services.files import parse_date

STATUS_LABELS = {"borrador": "Borrador", "por_autorizar": "Por autorizar", "autorizada": "Autorizada",
                 "recibida": "Recibida", "cancelada": "Cancelada"}
ORIGINS = {"nacional": "Nacional", "importado": "Importado"}
# Estados en los que la orden todavía se puede cancelar (una recibida ya movió inventario).
CANCELABLE = ("borrador", "por_autorizar", "autorizada")
MAX_ITEMS = 5  # renglones que captura el formulario de alta


# ------------------------------------------------------------------ proveedores
def create_supplier(db: Session, data: dict, actor_id: str | None) -> Supplier:
    name = (data.get("name") or "").strip()
    if not name:
        raise DomainError("El proveedor necesita nombre")
    if db.scalar(select(Supplier).where(func.lower(Supplier.name) == name.lower())):
        raise DomainError(f"Ya existe un proveedor con el nombre {name}")
    origin = data.get("origin") or "nacional"
    if origin not in ORIGINS:
        raise DomainError(f"Origen no válido: {origin}")
    s = Supplier(name=name[:200], origin=origin, email=norm_email(data.get("email") or None),
                 phone=norm_phone(data.get("phone") or None),
                 contact_name=(data.get("contact_name") or None), notes=(data.get("notes") or None))
    db.add(s)
    db.flush()
    record(db, actor_id, "proveedor.alta", "supplier", s.id,
           after={"nombre": s.name, "origen": s.origin, "correo": s.email, "telefono": s.phone},
           summary=f"Proveedor creado: {s.name}")
    db.commit()
    return s


def update_supplier(db: Session, supplier_id: str, data: dict, actor_id: str | None) -> Supplier:
    s = get_or_404(db, Supplier, supplier_id, "Proveedor")
    before = {"nombre": s.name, "origen": s.origin, "correo": s.email, "telefono": s.phone,
              "contacto": s.contact_name, "activo": s.is_active}
    if (data.get("name") or "").strip():
        s.name = data["name"].strip()[:200]
    if data.get("origin"):
        if data["origin"] not in ORIGINS:
            raise DomainError(f"Origen no válido: {data['origin']}")
        s.origin = data["origin"]
    if "email" in data:
        s.email = norm_email(data.get("email") or None)
    if "phone" in data:
        s.phone = norm_phone(data.get("phone") or None)
    if "contact_name" in data:
        s.contact_name = data.get("contact_name") or None
    if "notes" in data:
        s.notes = data.get("notes") or None
    if "is_active" in data:
        s.is_active = str(data.get("is_active")) in ("1", "True", "true", "on")
    record(db, actor_id, "proveedor.cambio", "supplier", s.id, before=before,
           after={"nombre": s.name, "origen": s.origin, "correo": s.email, "telefono": s.phone,
                  "contacto": s.contact_name, "activo": s.is_active},
           summary=f"Proveedor actualizado: {s.name}")
    db.commit()
    return s


def suppliers(db: Session, only_active: bool = False) -> list[Supplier]:
    stmt = select(Supplier).order_by(Supplier.name)
    if only_active:
        stmt = stmt.where(Supplier.is_active.is_(True))
    return list(db.scalars(stmt))


# ------------------------------------------------------------------ órdenes de compra
def get(db: Session, po_id: str) -> PurchaseOrder:
    return get_or_404(db, PurchaseOrder, po_id, "Orden de compra")


def orders(db: Session, status: str | None = None, supplier_id: str | None = None,
           limit: int = 200) -> list[PurchaseOrder]:
    stmt = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).limit(limit)
    if status:
        if status not in STATUS_LABELS:
            raise DomainError(f"Estado no válido: {status}")
        stmt = stmt.where(PurchaseOrder.status == status)
    if supplier_id:
        stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)
    return list(db.scalars(stmt))


def create_order(db: Session, data: dict, items: list[dict], actor_id: str | None) -> PurchaseOrder:
    """Alta en borrador. El folio se numera por conteo, como los de cotización y caso."""
    supplier = get_or_404(db, Supplier, data.get("supplier_id") or "", "Proveedor")
    warehouse = (get_or_404(db, Warehouse, data["warehouse_id"], "Bodega")
                 if data.get("warehouse_id") else None)
    renglones = [it for it in (items or []) if it and it.get("product_id")]
    if not renglones:
        raise DomainError("La orden de compra necesita al menos un renglón")
    n = (db.scalar(select(func.count()).select_from(PurchaseOrder)) or 0) + 1
    po = PurchaseOrder(folio=f"OC-{n:04d}", supplier_id=supplier.id,
                       warehouse_id=warehouse.id if warehouse else None,
                       expected_date=parse_date(data.get("expected_date")),
                       notes=(data.get("notes") or None), owner_id=actor_id)
    for it in renglones:
        product = get_or_404(db, Product, it.get("product_id") or "", "Producto")
        po.items.append(PurchaseOrderItem(
            product_id=product.id,
            qty_kg=inventory.num(it.get("qty_kg"), f"la cantidad en kilos de {product.name}", minimum=0.001),
            unit_cost_mxn=inventory.num(it.get("unit_cost_mxn"), f"el costo por kilo de {product.name}",
                                        minimum=0)))
    db.add(po)
    db.flush()
    record(db, actor_id, "compra.alta", "purchase_order", po.id,
           after={"folio": po.folio, "proveedor": supplier.name, "renglones": len(po.items),
                  "kg": po.total_kg, "total_mxn": po.total_mxn, "estado": po.status},
           summary=f"Orden de compra {po.folio} a {supplier.name}: {po.total_kg:g} kg, ${po.total_mxn:,.2f}")
    db.commit()
    return po


def submit(db: Session, po_id: str, actor_id: str | None) -> PurchaseOrder:
    """Envía el borrador. Solo pide autorización si el monto supera el umbral configurado (E-07)."""
    po = get(db, po_id)
    if po.status != "borrador":
        raise DomainError(f"Solo se puede enviar una orden en borrador; {po.folio} está "
                          f"{STATUS_LABELS[po.status].lower()}")
    if not po.items:
        raise DomainError(f"{po.folio} no tiene renglones")
    before = {"estado": po.status}
    umbral = config.PO_AUTH_THRESHOLD_MXN
    po.status = "por_autorizar" if po.total_mxn > umbral else "autorizada"
    record(db, actor_id, "compra.enviada", "purchase_order", po.id, before=before,
           after={"estado": po.status, "total_mxn": po.total_mxn, "umbral_mxn": umbral},
           summary=(f"{po.folio} enviada por ${po.total_mxn:,.2f} → " +
                    ("requiere autorización" if po.status == "por_autorizar"
                     else f"autorizada automáticamente (umbral ${umbral:,.2f})")))
    db.commit()
    return po


def authorize(db: Session, po_id: str, actor_id: str | None) -> PurchaseOrder:
    po = get(db, po_id)
    if po.status != "por_autorizar":
        raise DomainError(f"Solo se autoriza una orden por autorizar; {po.folio} está "
                          f"{STATUS_LABELS[po.status].lower()}")
    before = {"estado": po.status}
    po.status, po.authorized_by, po.authorized_at = "autorizada", actor_id, utcnow()
    record(db, actor_id, "compra.autorizada", "purchase_order", po.id, before=before,
           after={"estado": po.status, "autorizada_por": actor_id, "total_mxn": po.total_mxn},
           summary=f"{po.folio} autorizada (${po.total_mxn:,.2f})")
    db.commit()
    return po


def cancel(db: Session, po_id: str, actor_id: str | None, motivo: str | None) -> PurchaseOrder:
    po = get(db, po_id)
    if po.status not in CANCELABLE:
        raise DomainError(f"No se puede cancelar {po.folio}: está {STATUS_LABELS[po.status].lower()}")
    motivo = (motivo or "").strip()
    if not motivo:
        raise DomainError("Cancelar una orden siempre necesita motivo")
    before = {"estado": po.status}
    po.status = "cancelada"
    po.notes = f"{po.notes}\nCancelada: {motivo}" if po.notes else f"Cancelada: {motivo}"
    record(db, actor_id, "compra.cancelada", "purchase_order", po.id, before=before,
           after={"estado": po.status, "motivo": motivo},
           summary=f"{po.folio} cancelada: {motivo}")
    db.commit()
    return po


def receive(db: Session, po_id: str, renglones: list[dict], actor_id: str | None,
            supplier_invoice: str | None = None) -> PurchaseOrder:
    """Recepción total o parcial: da de alta el lote y registra la entrada en inventario.

    Cada renglón: {item_id, qty_kg, lot_code, expires_on?, warehouse_id?}. Un renglón sin kilos se
    ignora, para que en la pantalla se pueda recibir solo parte de la orden.
    """
    po = get(db, po_id)
    if po.status != "autorizada":
        raise DomainError(f"Solo se recibe una orden autorizada; {po.folio} está "
                          f"{STATUS_LABELS[po.status].lower()}")
    # Primera pasada: validar todo antes de mover nada, para no dejar lotes sueltos si algo falla.
    plan = []
    for r in (renglones or []):
        if not r or not r.get("item_id"):
            continue
        qty = inventory.num(r.get("qty_kg"), "los kilos recibidos", required=False, minimum=0)
        if not qty:
            continue
        item = get_or_404(db, PurchaseOrderItem, r.get("item_id"), "Renglón de la orden")
        if item.order_id != po.id:
            raise DomainError(f"El renglón capturado no pertenece a la orden {po.folio}")
        pendiente = round(item.qty_kg - (item.received_kg or 0.0), 3)
        if qty - pendiente > 1e-6:
            raise DomainError(f"{item.product.name}: se intentan recibir {qty:g} kg y solo faltan "
                              f"{pendiente:g} kg en {po.folio}")
        warehouse_id = r.get("warehouse_id") or po.warehouse_id
        if not warehouse_id:
            raise DomainError(f"{item.product.name}: indica la bodega donde entra la mercancía")
        get_or_404(db, Warehouse, warehouse_id, "Bodega")
        code = (r.get("lot_code") or "").strip().upper()
        if not code:
            raise DomainError(f"{item.product.name}: captura el código de lote que trae la mercancía")
        plan.append({"item": item, "qty": qty, "warehouse_id": warehouse_id, "code": code,
                     "expires_on": r.get("expires_on") or None})
    if not plan:
        raise DomainError("Captura los kilos recibidos de al menos un renglón")

    # Segunda pasada: lote (nuevo o reutilizado) + entrada de inventario referida a la orden.
    detalle = []
    for p in plan:
        item = p["item"]
        lot = db.scalar(select(Lot).where(Lot.product_id == item.product_id, Lot.code == p["code"]))
        if lot is None:
            lot = inventory.create_lot(db, {"product_id": item.product_id, "code": p["code"],
                                            "expires_on": p["expires_on"], "supplier_id": po.supplier_id,
                                            "notes": f"Recibido en {po.folio}"}, actor_id)
        inventory.move(db, type="entrada", product_id=item.product_id, warehouse_id=p["warehouse_id"],
                       qty_kg=p["qty"], lot_id=lot.id, actor_id=actor_id,
                       reason=f"Recepción de {po.folio}", ref_type="orden_compra", ref_id=po.id,
                       commit=False)
        item.received_kg = round((item.received_kg or 0.0) + p["qty"], 3)
        item.lot_id = lot.id
        detalle.append({"producto": item.product.name, "lote": lot.code, "kg": p["qty"]})

    before = {"estado": po.status, "factura_proveedor": po.supplier_invoice}
    if supplier_invoice and str(supplier_invoice).strip():
        po.supplier_invoice = str(supplier_invoice).strip()[:40]
    completa = all((i.received_kg or 0.0) + 1e-6 >= i.qty_kg for i in po.items)
    if completa:
        po.status, po.received_at = "recibida", utcnow()
    kg = round(sum(d["kg"] for d in detalle), 3)
    record(db, actor_id, "compra.recepcion", "purchase_order", po.id, before=before,
           after={"estado": po.status, "kg_recibidos": kg, "renglones": detalle,
                  "factura_proveedor": po.supplier_invoice, "completa": completa},
           summary=f"Recepción {'completa' if completa else 'parcial'} de {po.folio}: {kg:g} kg")
    db.commit()
    return po


def pending_kg(po: PurchaseOrder) -> float:
    return round(sum(max(i.qty_kg - (i.received_kg or 0.0), 0.0) for i in po.items), 3)


# ------------------------------------------------------------------ precios y métricas
def price_history(db: Session, product_id: str, limit: int = 30) -> dict:
    """Últimos costos de un producto, por compra y resumidos por proveedor.

    Sirve para comparar precios sin construir un comparador aparte: el comprador ve a qué le compró
    cada proveedor la última vez y su promedio ponderado por kilo.
    """
    product = get_or_404(db, Product, product_id, "Producto")
    stmt = (select(PurchaseOrderItem, PurchaseOrder)
            .join(PurchaseOrder, PurchaseOrderItem.order_id == PurchaseOrder.id)
            .where(PurchaseOrderItem.product_id == product.id, PurchaseOrder.status != "cancelada")
            .order_by(PurchaseOrder.created_at.desc()).limit(limit))
    compras, por_proveedor = [], {}
    for item, po in db.execute(stmt).all():
        compras.append({"folio": po.folio, "purchase_order_id": po.id, "proveedor": po.supplier.name,
                        "supplier_id": po.supplier_id, "fecha": po.created_at, "estado": po.status,
                        "kg": item.qty_kg, "costo_unitario_mxn": item.unit_cost_mxn})
        acc = por_proveedor.setdefault(po.supplier_id, {
            "supplier_id": po.supplier_id, "proveedor": po.supplier.name, "compras": 0, "kg": 0.0,
            "importe_mxn": 0.0, "ultimo_costo_mxn": item.unit_cost_mxn, "ultima_fecha": po.created_at})
        acc["compras"] += 1
        acc["kg"] = round(acc["kg"] + item.qty_kg, 3)
        acc["importe_mxn"] = round(acc["importe_mxn"] + item.qty_kg * (item.unit_cost_mxn or 0.0), 2)
    for acc in por_proveedor.values():
        acc["costo_promedio_mxn"] = round(acc["importe_mxn"] / acc["kg"], 2) if acc["kg"] else None
    return {"product_id": product.id, "producto": product.name, "sku": product.sku, "compras": compras,
            "por_proveedor": sorted(por_proveedor.values(), key=lambda a: a["ultima_fecha"], reverse=True)}


def metrics(db: Session) -> dict:
    por_estado = {s: 0 for s in STATUS_LABELS}
    for status, n in db.execute(select(PurchaseOrder.status, func.count())
                                .group_by(PurchaseOrder.status)).all():
        por_estado[status] = int(n)
    vigentes = PurchaseOrder.status != "cancelada"  # una orden cancelada no es gasto
    gasto = {}
    for name, importe in db.execute(
            select(Supplier.name, func.sum(PurchaseOrderItem.qty_kg * PurchaseOrderItem.unit_cost_mxn))
            .join(PurchaseOrder, PurchaseOrder.supplier_id == Supplier.id)
            .join(PurchaseOrderItem, PurchaseOrderItem.order_id == PurchaseOrder.id)
            .where(vigentes).group_by(Supplier.name)).all():
        gasto[name] = round(float(importe or 0.0), 2)
    costo_kg = {}
    for name, kg, importe in db.execute(
            select(Product.name, func.sum(PurchaseOrderItem.qty_kg),
                   func.sum(PurchaseOrderItem.qty_kg * PurchaseOrderItem.unit_cost_mxn))
            .join(PurchaseOrderItem, PurchaseOrderItem.product_id == Product.id)
            .join(PurchaseOrder, PurchaseOrderItem.order_id == PurchaseOrder.id)
            .where(vigentes).group_by(Product.name)).all():
        if kg:
            costo_kg[name] = round(float(importe or 0.0) / float(kg), 2)
    return {"por_estado": por_estado,
            "gasto_por_proveedor": dict(sorted(gasto.items(), key=lambda kv: -kv[1])),
            "gasto_total_mxn": round(sum(gasto.values()), 2),
            "costo_promedio_kg": dict(sorted(costo_kg.items(), key=lambda kv: kv[0])),
            "pendientes_autorizar": por_estado.get("por_autorizar", 0),
            "pendientes_recibir": por_estado.get("autorizada", 0)}
