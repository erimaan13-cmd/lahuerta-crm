"""Inventario: bodegas, lotes y movimientos.

Decisiones que implementa (AT-15):
- E-02 la unidad de manejo se configura por producto y siempre se guarda su equivalencia en kilos,
  porque el negocio reporta en kilos.
- E-04 lote y caducidad de captura manual.
- E-05 existencia por producto + lote + bodega.
- E-06 la existencia se descuenta sola: cada entrada, salida o ajuste es un movimiento con actor.

La existencia NO se guarda en una columna: es la suma de los movimientos. Así nunca queda un saldo
que contradiga su historial, y cualquier diferencia se puede rastrear renglón por renglón.
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import config
from app.audit import record
from app.models import Lot, Product, StockMovement, Warehouse, utcnow
from app.services.common import DomainError, get_or_404
from app.services.files import parse_date

TYPES = {"entrada", "salida", "ajuste", "traspaso"}
UNITS = {"kg": "Kilogramos", "saco": "Saco", "caja": "Caja", "tarima": "Tarima"}
PACKAGING = {"saco_pp": "Saco de polipropileno", "saco_kraft": "Saco de papel kraft",
             "caja_corrugado": "Caja de cartón corrugado", "granel": "A granel"}


def num(value, field: str, *, required: bool = True, minimum: float | None = None) -> float | None:
    if value in (None, ""):
        if required:
            raise DomainError(f"Falta {field}")
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise DomainError(f"{field} debe ser un número: {value}")
    if minimum is not None and v < minimum:
        raise DomainError(f"{field} debe ser mayor o igual a {minimum:g}")
    return v


def to_kg(product: Product, qty: float, unit: str | None = None) -> float:
    """Convierte una cantidad en la unidad de manejo a kilos (E-02)."""
    unit = unit or product.unit or "kg"
    if unit == "kg":
        return round(qty, 3)
    return round(qty * (product.kg_per_unit or 1.0), 3)


# ------------------------------------------------------------------ catálogos
def create_warehouse(db: Session, data: dict, actor_id: str | None) -> Warehouse:
    code = (data.get("code") or "").strip().upper()
    name = (data.get("name") or "").strip()
    if not code or not name:
        raise DomainError("La bodega necesita clave y nombre")
    if db.scalar(select(Warehouse).where(Warehouse.code == code)):
        raise DomainError(f"Ya existe una bodega con la clave {code}")
    w = Warehouse(code=code[:20], name=name[:120], address=(data.get("address") or None))
    db.add(w)
    db.flush()
    record(db, actor_id, "bodega.alta", "warehouse", w.id, after={"clave": w.code, "nombre": w.name},
           summary=f"Bodega creada: {w.code} — {w.name}")
    db.commit()
    return w


def create_product(db: Session, data: dict, actor_id: str | None) -> Product:
    sku = (data.get("sku") or "").strip().upper()
    name = (data.get("name") or "").strip()
    if not sku or not name:
        raise DomainError("El producto necesita clave (SKU) y nombre")
    if db.scalar(select(Product).where(Product.sku == sku)):
        raise DomainError(f"Ya existe un producto con la clave {sku}")
    unit = data.get("unit") or "kg"
    if unit not in UNITS:
        raise DomainError(f"Unidad no válida: {unit}")
    kg_per_unit = num(data.get("kg_per_unit") or (1 if unit == "kg" else None), "los kilos por unidad",
                      minimum=0.001)
    p = Product(sku=sku[:40], name=name[:160], category=data.get("category") or "otro",
                keywords=data.get("keywords") or "", unit=unit, kg_per_unit=kg_per_unit,
                packaging=data.get("packaging") or None,
                min_stock_kg=num(data.get("min_stock_kg"), "el mínimo", required=False, minimum=0),
                shelf_life_days=int(data["shelf_life_days"]) if data.get("shelf_life_days") else None)
    db.add(p)
    db.flush()
    record(db, actor_id, "producto.alta", "product", p.id,
           after={"sku": p.sku, "nombre": p.name, "unidad": p.unit, "kg_por_unidad": p.kg_per_unit,
                  "minimo_kg": p.min_stock_kg},
           summary=f"Producto creado: {p.sku} — {p.name}")
    db.commit()
    return p


def update_product(db: Session, product_id: str, data: dict, actor_id: str | None) -> Product:
    p = get_or_404(db, Product, product_id, "Producto")
    before = {"unidad": p.unit, "kg_por_unidad": p.kg_per_unit, "minimo_kg": p.min_stock_kg,
              "empaque": p.packaging, "vida_util_dias": p.shelf_life_days}
    if data.get("unit"):
        if data["unit"] not in UNITS:
            raise DomainError(f"Unidad no válida: {data['unit']}")
        p.unit = data["unit"]
    if data.get("kg_per_unit") not in (None, ""):
        p.kg_per_unit = num(data["kg_per_unit"], "los kilos por unidad", minimum=0.001)
    if "packaging" in data:
        p.packaging = data.get("packaging") or None
    if "min_stock_kg" in data:
        p.min_stock_kg = num(data.get("min_stock_kg"), "el mínimo", required=False, minimum=0)
    if data.get("shelf_life_days") not in (None, ""):
        p.shelf_life_days = int(data["shelf_life_days"])
    record(db, actor_id, "producto.cambio", "product", p.id, before=before,
           after={"unidad": p.unit, "kg_por_unidad": p.kg_per_unit, "minimo_kg": p.min_stock_kg,
                  "empaque": p.packaging, "vida_util_dias": p.shelf_life_days},
           summary=f"Producto actualizado: {p.sku}")
    db.commit()
    return p


def create_lot(db: Session, data: dict, actor_id: str | None) -> Lot:
    product = get_or_404(db, Product, data.get("product_id"), "Producto")
    code = (data.get("code") or "").strip().upper()
    if not code:
        raise DomainError("El lote necesita un código")
    if db.scalar(select(Lot).where(Lot.product_id == product.id, Lot.code == code)):
        raise DomainError(f"El lote {code} ya existe para {product.name}")
    expires = parse_date(data.get("expires_on"))
    received = parse_date(data.get("received_on")) or utcnow()
    if expires is None and product.shelf_life_days:
        expires = received + timedelta(days=product.shelf_life_days)
    lot = Lot(product_id=product.id, code=code[:40], expires_on=expires, received_on=received,
              supplier_id=data.get("supplier_id") or None, notes=data.get("notes") or None)
    db.add(lot)
    db.flush()
    record(db, actor_id, "lote.alta", "lot", lot.id,
           after={"producto": product.name, "lote": lot.code,
                  "caduca": expires.date().isoformat() if expires else None},
           summary=f"Lote {lot.code} de {product.name}")
    db.commit()
    return lot


# ------------------------------------------------------------------ movimientos
def _balance_stmt(product_id=None, warehouse_id=None, lot_id=None):
    stmt = select(func.coalesce(func.sum(StockMovement.qty_kg), 0.0))
    if product_id:
        stmt = stmt.where(StockMovement.product_id == product_id)
    if warehouse_id:
        stmt = stmt.where(StockMovement.warehouse_id == warehouse_id)
    if lot_id:
        stmt = stmt.where(StockMovement.lot_id == lot_id)
    return stmt


def balance(db: Session, product_id: str | None = None, warehouse_id: str | None = None,
            lot_id: str | None = None) -> float:
    return round(float(db.scalar(_balance_stmt(product_id, warehouse_id, lot_id)) or 0.0), 3)


def lot_balance(db: Session, lot_id: str) -> float:
    return balance(db, lot_id=lot_id)


def move(db: Session, *, type: str, product_id: str, warehouse_id: str, qty_kg: float, actor_id: str | None,
         lot_id: str | None = None, reason: str | None = None, ref_type: str | None = None,
         ref_id: str | None = None, commit: bool = True) -> StockMovement:
    """Registra un movimiento. `qty_kg` va con signo: positivo entra, negativo sale.

    Nunca deja existencia negativa: es la única forma de que el inventario sirva para algo.
    """
    if type not in TYPES:
        raise DomainError(f"Tipo de movimiento no válido: {type}")
    product = get_or_404(db, Product, product_id, "Producto")
    warehouse = get_or_404(db, Warehouse, warehouse_id, "Bodega")
    qty = num(qty_kg, "la cantidad en kilos")
    if qty == 0:
        raise DomainError("La cantidad no puede ser cero")
    lot = get_or_404(db, Lot, lot_id, "Lote") if lot_id else None
    if lot and lot.product_id != product.id:
        raise DomainError(f"El lote {lot.code} no pertenece a {product.name}")
    if qty < 0:
        disponible = balance(db, product.id, warehouse.id, lot.id if lot else None)
        if disponible + qty < -1e-6:
            donde = f"{warehouse.code}" + (f", lote {lot.code}" if lot else "")
            raise DomainError(f"No hay existencia suficiente de {product.name} en {donde}: "
                              f"disponible {disponible:g} kg, se intentan sacar {abs(qty):g} kg")
    mv = StockMovement(type=type, product_id=product.id, lot_id=lot.id if lot else None,
                       warehouse_id=warehouse.id, qty_kg=qty, reason=reason, ref_type=ref_type,
                       ref_id=ref_id, actor_id=actor_id)
    db.add(mv)
    db.flush()
    record(db, actor_id, f"inventario.{type}", "product", product.id,
           after={"producto": product.name, "lote": lot.code if lot else None, "bodega": warehouse.code,
                  "kg": qty, "motivo": reason, "referencia": f"{ref_type or ''}:{ref_id or ''}".strip(":"),
                  "existencia_resultante": balance(db, product.id, warehouse.id, lot.id if lot else None)},
           summary=f"{type.capitalize()} de {abs(qty):g} kg · {product.name} · {warehouse.code}")
    if commit:
        db.commit()
    return mv


def register(db: Session, data: dict, actor_id: str | None) -> StockMovement:
    """Alta manual desde la interfaz (entrada, salida o ajuste)."""
    kind = data.get("type") or "entrada"
    product = get_or_404(db, Product, data.get("product_id"), "Producto")
    qty = num(data.get("qty"), "la cantidad")
    unit = data.get("unit") or "kg"
    if unit not in UNITS:
        raise DomainError(f"Unidad no válida: {unit}")
    kg = to_kg(product, qty, unit)
    if kind == "salida":
        kg = -abs(kg)
    elif kind == "entrada":
        kg = abs(kg)
    elif kind == "ajuste" and not data.get("reason"):
        raise DomainError("Un ajuste siempre necesita motivo")
    return move(db, type=kind, product_id=product.id, warehouse_id=data.get("warehouse_id"), qty_kg=kg,
                lot_id=data.get("lot_id") or None, reason=data.get("reason") or None, ref_type="manual",
                actor_id=actor_id)


def transfer(db: Session, data: dict, actor_id: str | None) -> list[StockMovement]:
    """Traspaso entre bodegas: una salida y una entrada, con la misma referencia."""
    product = get_or_404(db, Product, data.get("product_id"), "Producto")
    origen, destino = data.get("from_warehouse_id"), data.get("to_warehouse_id")
    if not origen or not destino or origen == destino:
        raise DomainError("El traspaso necesita una bodega de origen y otra distinta de destino")
    kg = to_kg(product, num(data.get("qty"), "la cantidad"), data.get("unit") or "kg")
    lot_id = data.get("lot_id") or None
    ref = f"traspaso:{utcnow().isoformat(timespec='seconds')}"
    out = move(db, type="traspaso", product_id=product.id, warehouse_id=origen, qty_kg=-abs(kg), lot_id=lot_id,
               reason=data.get("reason") or "Traspaso entre bodegas", ref_type="traspaso", ref_id=ref,
               actor_id=actor_id, commit=False)
    into = move(db, type="traspaso", product_id=product.id, warehouse_id=destino, qty_kg=abs(kg), lot_id=lot_id,
                reason=data.get("reason") or "Traspaso entre bodegas", ref_type="traspaso", ref_id=ref,
                actor_id=actor_id, commit=False)
    db.commit()
    return [out, into]


# ------------------------------------------------------------------ consultas
def stock_rows(db: Session, product_id: str | None = None, warehouse_id: str | None = None) -> list[dict]:
    """Existencia por producto + lote + bodega (solo lo que tiene saldo)."""
    stmt = (select(StockMovement.product_id, StockMovement.lot_id, StockMovement.warehouse_id,
                   func.sum(StockMovement.qty_kg))
            .group_by(StockMovement.product_id, StockMovement.lot_id, StockMovement.warehouse_id))
    if product_id:
        stmt = stmt.where(StockMovement.product_id == product_id)
    if warehouse_id:
        stmt = stmt.where(StockMovement.warehouse_id == warehouse_id)
    rows = []
    for pid, lid, wid, kg in db.execute(stmt).all():
        if abs(kg or 0) < 1e-6:
            continue
        product, lot, wh = db.get(Product, pid), (db.get(Lot, lid) if lid else None), db.get(Warehouse, wid)
        rows.append({"product": product, "lot": lot, "warehouse": wh, "kg": round(float(kg), 3),
                     "expires_on": lot.expires_on if lot else None})
    rows.sort(key=lambda r: (r["product"].name, r["warehouse"].code, r["lot"].code if r["lot"] else ""))
    return rows


def by_product(db: Session) -> list[dict]:
    """Totales por producto, con su mínimo configurado."""
    totals = dict(db.execute(select(StockMovement.product_id, func.sum(StockMovement.qty_kg))
                             .group_by(StockMovement.product_id)).all())
    out = []
    for p in db.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.name)):
        kg = round(float(totals.get(p.id) or 0.0), 3)
        out.append({"product": p, "kg": kg, "min_kg": p.min_stock_kg,
                    "below": p.min_stock_kg is not None and kg < p.min_stock_kg,
                    "units": round(kg / (p.kg_per_unit or 1.0), 2) if p.unit != "kg" else kg})
    return out


def low_stock(db: Session) -> list[dict]:
    return [r | {"min_kg": r["min_kg"] or 0} for r in by_product(db) if r["below"]]


def expiring_lots(db: Session, days: int | None = None) -> list[dict]:
    limit = utcnow() + timedelta(days=days if days is not None else config.LOT_EXPIRY_ALERT_DAYS)
    out = []
    for lot in db.scalars(select(Lot).where(Lot.expires_on.is_not(None), Lot.expires_on <= limit)
                          .order_by(Lot.expires_on)):
        kg = lot_balance(db, lot.id)
        if kg > 0:
            out.append({"lot": lot, "kg": kg, "expires_on": lot.expires_on})
    return out


def movements(db: Session, product_id: str | None = None, warehouse_id: str | None = None,
              limit: int = 200) -> list[StockMovement]:
    stmt = select(StockMovement).order_by(StockMovement.at.desc()).limit(limit)
    if product_id:
        stmt = stmt.where(StockMovement.product_id == product_id)
    if warehouse_id:
        stmt = stmt.where(StockMovement.warehouse_id == warehouse_id)
    return list(db.scalars(stmt))


def metrics(db: Session) -> dict:
    rows = by_product(db)
    total = round(sum(r["kg"] for r in rows), 2)
    por_bodega = {}
    for pid, wid, kg in db.execute(select(StockMovement.product_id, StockMovement.warehouse_id,
                                          func.sum(StockMovement.qty_kg))
                                   .group_by(StockMovement.product_id, StockMovement.warehouse_id)).all():
        wh = db.get(Warehouse, wid)
        por_bodega[wh.name] = round(por_bodega.get(wh.name, 0.0) + float(kg or 0), 2)
    top = sorted([r for r in rows if r["kg"] > 0], key=lambda r: -r["kg"])[:8]
    return {"kg_total": total, "productos_con_existencia": sum(1 for r in rows if r["kg"] > 0),
            "bajo_minimo": len([r for r in rows if r["below"]]),
            "lotes_por_caducar": len(expiring_lots(db)),
            "kg_por_bodega": {k: v for k, v in sorted(por_bodega.items(), key=lambda kv: -kv[1])},
            "top_productos": [{"nombre": r["product"].name, "kg": r["kg"]} for r in top]}
