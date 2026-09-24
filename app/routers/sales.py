"""Ventas: pedidos (alta, confirmación, entrega, cancelación y captura del folio de factura).

Las rutas solo validan permisos y delegan en `app/services/sales.py`; el descuento de inventario lo
hace ese servicio a través de `app/services/inventory.py`, nunca aquí.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import db as dbmod
from app.models import Account, Lot, Product, SalesOrder, User, Warehouse
from app.services import files as files_svc, inventory, sales
from app.services.common import get_or_404
from app.web import back, csrf_protect, entity_history, form_dict, render, require, ser

router = APIRouter(tags=["ventas"])


def _catalogos(db: Session) -> dict:
    """Listas para los formularios: cuentas, bodegas, productos y lotes con su caducidad."""
    return {"accounts": list(db.scalars(select(Account).order_by(Account.name))),
            "warehouses": list(db.scalars(select(Warehouse).where(Warehouse.is_active.is_(True))
                                          .order_by(Warehouse.code))),
            "products": list(db.scalars(select(Product).where(Product.is_active.is_(True))
                                        .order_by(Product.name))),
            "lots": list(db.scalars(select(Lot).order_by(Lot.expires_on))),
            "units": sorted(inventory.UNITS.items()),
            "STATUS_LABELS": sales.STATUS_LABELS, "n_items": range(sales.MAX_ITEMS_UI)}


# ------------------------------------------------------------------ interfaz
@router.get("/ventas", response_class=HTMLResponse)
def ui_orders(request: Request, status: str | None = None, db: Session = Depends(dbmod.get_db),
              user: User = Depends(require("sales:read"))):
    return render(request, "ventas.html", user, orders=sales.listing(db, status or None),
                  status=status, m=sales.metrics(db), **_catalogos(db))


@router.post("/ventas", dependencies=[Depends(csrf_protect)])
async def ui_create_order(request: Request, db: Session = Depends(dbmod.get_db),
                          user: User = Depends(require("sales:write"))):
    f = await form_dict(request)
    items = [{"product_id": f.get(f"product_id_{i}"), "qty": f.get(f"qty_{i}"), "unit": f.get(f"unit_{i}"),
              "unit_price_mxn": f.get(f"unit_price_mxn_{i}"), "lot_id": f.get(f"lot_id_{i}")}
             for i in range(sales.MAX_ITEMS_UI) if f.get(f"product_id_{i}")]
    order = sales.create_order(db, f, items, user.id)
    return back(f"/ventas/{order.id}")


@router.get("/ventas/{order_id}", response_class=HTMLResponse)
def ui_order(order_id: str, request: Request, db: Session = Depends(dbmod.get_db),
             user: User = Depends(require("sales:read"))):
    order = get_or_404(db, SalesOrder, order_id, "Pedido")
    return render(request, "venta_detalle.html", user, **entity_history(db, user, order.id), o=order,
                  movimientos=sales.movements_of(db, order.id),
                  docs=files_svc.for_entity(db, "sales_order", order.id),
                  entity_type="sales_order", entity_id=order.id, next=f"/ventas/{order.id}",
                  STATUS_LABELS=sales.STATUS_LABELS)


@router.post("/ventas/{order_id}/confirmar", dependencies=[Depends(csrf_protect)])
def ui_confirm(order_id: str, db: Session = Depends(dbmod.get_db),
               user: User = Depends(require("sales:write"))):
    sales.confirm(db, order_id, user.id)
    return back(f"/ventas/{order_id}")


@router.post("/ventas/{order_id}/entregar", dependencies=[Depends(csrf_protect)])
def ui_deliver(order_id: str, db: Session = Depends(dbmod.get_db),
               user: User = Depends(require("sales:write"))):
    sales.deliver(db, order_id, user.id)
    return back(f"/ventas/{order_id}")


@router.post("/ventas/{order_id}/cancelar", dependencies=[Depends(csrf_protect)])
async def ui_cancel(order_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                    user: User = Depends(require("sales:write"))):
    f = await form_dict(request)
    sales.cancel(db, order_id, user.id, f.get("motivo"))
    return back(f"/ventas/{order_id}")


@router.post("/ventas/{order_id}/factura", dependencies=[Depends(csrf_protect)])
async def ui_invoice(order_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                     user: User = Depends(require("sales:write"))):
    f = await form_dict(request)
    sales.set_invoice(db, order_id, f.get("invoice_folio"), user.id)
    return back(f"/ventas/{order_id}")


# ------------------------------------------------------------------ API REST
@router.get("/api/ventas")
def api_orders(status: str | None = None, account_id: str | None = None,
               db: Session = Depends(dbmod.get_db), user: User = Depends(require("sales:read"))):
    return [{**ser(o), "total_kg": o.total_kg, "total_mxn": o.total_mxn, "items": ser(o.items)}
            for o in sales.listing(db, status, account_id)]


@router.post("/api/ventas", status_code=201)
async def api_create_order(request: Request, db: Session = Depends(dbmod.get_db),
                           user: User = Depends(require("sales:write"))):
    body = await request.json()
    order = sales.create_order(db, body, body.get("items") or [], user.id)
    return {"order": ser(order), "items": ser(order.items), "total_kg": order.total_kg,
            "total_mxn": order.total_mxn}


@router.post("/api/ventas/{order_id}/entregar")
def api_deliver(order_id: str, db: Session = Depends(dbmod.get_db),
                user: User = Depends(require("sales:write"))):
    order = sales.deliver(db, order_id, user.id)
    return {"order": ser(order), "movimientos": ser(sales.movements_of(db, order.id))}


@router.get("/api/ventas/metricas")
def api_metrics(db: Session = Depends(dbmod.get_db), user: User = Depends(require("sales:read"))):
    m = sales.metrics(db)
    return {**m, "pendientes": ser(m["pendientes"])}
