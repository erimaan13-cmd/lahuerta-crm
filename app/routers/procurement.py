"""Abastecimiento: proveedores y órdenes de compra (alta, autorización y recepción).

Las rutas solo validan permisos y delegan en `app.services.procurement`. La recepción es la única
operación que toca inventario, y lo hace a través del servicio de inventario.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import db as dbmod
from app.models import Product, User, Warehouse
from app.services import files as files_svc, inventory, procurement
from app.web import back, csrf_protect, entity_history, form_dict, render, require, ser

router = APIRouter(tags=["abastecimiento"])


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


def _resumen(po) -> dict:
    """Orden en formato plano para la API (sin objetos del ORM ni fechas sin serializar)."""
    return {"id": po.id, "folio": po.folio, "estado": po.status, "proveedor": po.supplier.name,
            "supplier_id": po.supplier_id, "bodega": po.warehouse.code if po.warehouse else None,
            "total_kg": po.total_kg, "total_mxn": po.total_mxn,
            "pendiente_kg": procurement.pending_kg(po), "factura_proveedor": po.supplier_invoice,
            "creada": _iso(po.created_at), "esperada": _iso(po.expected_date),
            "recibida": _iso(po.received_at),
            "renglones": [{"item_id": i.id, "product_id": i.product_id, "producto": i.product.name,
                           "kg": i.qty_kg, "costo_unitario_mxn": i.unit_cost_mxn,
                           "recibido_kg": i.received_kg, "lote": i.lot.code if i.lot else None}
                          for i in po.items]}


def _renglones_form(f: dict) -> list[dict]:
    """Lee los renglones numerados del formulario de alta (producto_0…producto_4)."""
    return [{"product_id": f.get(f"product_id_{i}"), "qty_kg": f.get(f"qty_kg_{i}"),
             "unit_cost_mxn": f.get(f"unit_cost_mxn_{i}")}
            for i in range(procurement.MAX_ITEMS) if f.get(f"product_id_{i}")]


def _recepcion_form(f: dict) -> list[dict]:
    """Lee la captura de recepción (un renglón por partida de la orden)."""
    out = []
    for i in range(50):
        if not f.get(f"item_id_{i}"):
            continue
        out.append({"item_id": f.get(f"item_id_{i}"), "qty_kg": f.get(f"qty_kg_{i}"),
                    "lot_code": f.get(f"lot_code_{i}"), "expires_on": f.get(f"expires_on_{i}"),
                    "warehouse_id": f.get(f"warehouse_id_{i}") or f.get("warehouse_id")})
    return out


# ======================================================================= interfaz
@router.get("/abastecimiento", response_class=HTMLResponse)
def ui_orders(request: Request, status: str | None = None, db: Session = Depends(dbmod.get_db),
              user: User = Depends(require("procurement:read"))):
    return render(request, "abastecimiento.html", user, orders=procurement.orders(db, status or None),
                  m=procurement.metrics(db), status=status, statuses=procurement.STATUS_LABELS,
                  suppliers=procurement.suppliers(db, only_active=True),
                  products=list(db.scalars(select(Product).where(Product.is_active.is_(True))
                                           .order_by(Product.name))),
                  warehouses=list(db.scalars(select(Warehouse).where(Warehouse.is_active.is_(True))
                                             .order_by(Warehouse.code))),
                  max_items=procurement.MAX_ITEMS)


@router.get("/abastecimiento/proveedores", response_class=HTMLResponse)
def ui_suppliers(request: Request, db: Session = Depends(dbmod.get_db),
                 user: User = Depends(require("procurement:read"))):
    return render(request, "abastecimiento_proveedores.html", user,
                  suppliers=procurement.suppliers(db), origins=procurement.ORIGINS)


@router.post("/abastecimiento/proveedores", dependencies=[Depends(csrf_protect)])
async def ui_create_supplier(request: Request, db: Session = Depends(dbmod.get_db),
                             user: User = Depends(require("procurement:write"))):
    procurement.create_supplier(db, await form_dict(request), user.id)
    return back("/abastecimiento/proveedores")


@router.post("/abastecimiento/proveedores/{supplier_id}", dependencies=[Depends(csrf_protect)])
async def ui_update_supplier(supplier_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                             user: User = Depends(require("procurement:write"))):
    procurement.update_supplier(db, supplier_id, await form_dict(request), user.id)
    return back("/abastecimiento/proveedores")


@router.post("/abastecimiento", dependencies=[Depends(csrf_protect)])
async def ui_create_order(request: Request, db: Session = Depends(dbmod.get_db),
                          user: User = Depends(require("procurement:write"))):
    f = await form_dict(request)
    po = procurement.create_order(db, f, _renglones_form(f), user.id)
    return back(f"/abastecimiento/{po.id}")


@router.get("/abastecimiento/{po_id}", response_class=HTMLResponse)
def ui_order(po_id: str, request: Request, db: Session = Depends(dbmod.get_db),
             user: User = Depends(require("procurement:read"))):
    po = procurement.get(db, po_id)
    vistos, precios = set(), []
    for it in po.items:  # historial de precios de lo que se está comprando (comparación sin pantalla aparte)
        if it.product_id not in vistos:
            vistos.add(it.product_id)
            precios.append(procurement.price_history(db, it.product_id))
    return render(request, "abastecimiento_detalle.html", user, **entity_history(db, user, po.id), po=po,
                  statuses=procurement.STATUS_LABELS, precios=precios,
                  pendiente_kg=procurement.pending_kg(po),
                  docs=files_svc.for_entity(db, "purchase_order", po.id),
                  entity_type="purchase_order", entity_id=po.id, next=f"/abastecimiento/{po.id}",
                  warehouses=list(db.scalars(select(Warehouse).where(Warehouse.is_active.is_(True))
                                             .order_by(Warehouse.code))))


@router.post("/abastecimiento/{po_id}/enviar", dependencies=[Depends(csrf_protect)])
def ui_submit(po_id: str, db: Session = Depends(dbmod.get_db),
              user: User = Depends(require("procurement:write"))):
    procurement.submit(db, po_id, user.id)
    return back(f"/abastecimiento/{po_id}")


@router.post("/abastecimiento/{po_id}/autorizar", dependencies=[Depends(csrf_protect)])
def ui_authorize(po_id: str, db: Session = Depends(dbmod.get_db),
                 user: User = Depends(require("procurement:authorize"))):
    procurement.authorize(db, po_id, user.id)
    return back(f"/abastecimiento/{po_id}")


@router.post("/abastecimiento/{po_id}/recibir", dependencies=[Depends(csrf_protect)])
async def ui_receive(po_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                     user: User = Depends(require("procurement:write"))):
    f = await form_dict(request)
    procurement.receive(db, po_id, _recepcion_form(f), user.id,
                        supplier_invoice=f.get("supplier_invoice"))
    return back(f"/abastecimiento/{po_id}")


@router.post("/abastecimiento/{po_id}/cancelar", dependencies=[Depends(csrf_protect)])
async def ui_cancel(po_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                    user: User = Depends(require("procurement:write"))):
    procurement.cancel(db, po_id, user.id, (await form_dict(request)).get("motivo"))
    return back(f"/abastecimiento/{po_id}")


# ======================================================================= API REST (JSON)
@router.get("/api/abastecimiento")
def api_orders(status: str | None = None, supplier_id: str | None = None,
               db: Session = Depends(dbmod.get_db), user: User = Depends(require("procurement:read"))):
    return {"metricas": procurement.metrics(db),
            "ordenes": [_resumen(po) for po in procurement.orders(db, status, supplier_id)]}


@router.post("/api/abastecimiento", status_code=201)
async def api_create_order(request: Request, db: Session = Depends(dbmod.get_db),
                           user: User = Depends(require("procurement:write"))):
    body = await request.json()
    po = procurement.create_order(db, body, body.get("items") or [], user.id)
    return JSONResponse({"orden": _resumen(po), "registro": ser(po)}, status_code=201)


@router.post("/api/abastecimiento/{po_id}/enviar")
def api_submit(po_id: str, db: Session = Depends(dbmod.get_db),
               user: User = Depends(require("procurement:write"))):
    return _resumen(procurement.submit(db, po_id, user.id))


@router.post("/api/abastecimiento/{po_id}/autorizar")
def api_authorize(po_id: str, db: Session = Depends(dbmod.get_db),
                  user: User = Depends(require("procurement:authorize"))):
    return _resumen(procurement.authorize(db, po_id, user.id))


@router.post("/api/abastecimiento/{po_id}/recibir")
async def api_receive(po_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                      user: User = Depends(require("procurement:write"))):
    body = await request.json()
    po = procurement.receive(db, po_id, body.get("renglones") or [], user.id,
                             supplier_invoice=body.get("supplier_invoice"))
    return {"orden": _resumen(po),
            "existencias": [{"product_id": i.product_id, "kg": inventory.balance(db, i.product_id)}
                            for i in po.items]}


@router.post("/api/abastecimiento/{po_id}/cancelar")
async def api_cancel(po_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                     user: User = Depends(require("procurement:write"))):
    return _resumen(procurement.cancel(db, po_id, user.id, (await request.json()).get("motivo")))


@router.get("/api/abastecimiento/precios/{product_id}")
def api_prices(product_id: str, db: Session = Depends(dbmod.get_db),
               user: User = Depends(require("procurement:read"))):
    return procurement.price_history(db, product_id)


@router.post("/api/abastecimiento/proveedores", status_code=201)
async def api_create_supplier(request: Request, db: Session = Depends(dbmod.get_db),
                              user: User = Depends(require("procurement:write"))):
    return JSONResponse(ser(procurement.create_supplier(db, await request.json(), user.id)),
                        status_code=201)
