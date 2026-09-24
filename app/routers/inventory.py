"""Inventario: existencias, movimientos, lotes, productos y bodegas.

Las rutas solo validan permisos y delegan en `app.services.inventory`; la existencia nunca se calcula
aquí (es la suma de los movimientos, ver el servicio).
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import db as dbmod
from app.models import Lot, Product, User, Warehouse
from app.services import inventory
from app.web import back, csrf_protect, form_dict, render, require, ser

router = APIRouter(tags=["inventario"])


def _catalogos(db: Session) -> dict:
    """Listas que necesitan casi todas las pantallas del módulo."""
    return {"products": list(db.scalars(select(Product).where(Product.is_active.is_(True))
                                        .order_by(Product.name))),
            "warehouses": list(db.scalars(select(Warehouse).where(Warehouse.is_active.is_(True))
                                          .order_by(Warehouse.code))),
            "units": inventory.UNITS, "packaging": inventory.PACKAGING}


def _fila(r: dict) -> dict:
    """Existencia en formato plano para la API (sin objetos del ORM)."""
    return {"product_id": r["product"].id, "sku": r["product"].sku, "producto": r["product"].name,
            "lot_id": r["lot"].id if r["lot"] else None, "lote": r["lot"].code if r["lot"] else None,
            "warehouse_id": r["warehouse"].id, "bodega": r["warehouse"].code, "kg": r["kg"],
            "caduca": r["expires_on"].date().isoformat() if r["expires_on"] else None}


# ======================================================================= interfaz
@router.get("/inventario", response_class=HTMLResponse)
def ui_stock(request: Request, product_id: str | None = None, warehouse_id: str | None = None,
             db: Session = Depends(dbmod.get_db), user: User = Depends(require("inventory:read"))):
    return render(request, "inventario.html", user, m=inventory.metrics(db),
                  rows=inventory.stock_rows(db, product_id or None, warehouse_id or None),
                  totales=inventory.by_product(db), low=inventory.low_stock(db),
                  expiring=inventory.expiring_lots(db),
                  f={"product_id": product_id, "warehouse_id": warehouse_id}, **_catalogos(db))


@router.get("/inventario/movimientos", response_class=HTMLResponse)
def ui_movements(request: Request, product_id: str | None = None, warehouse_id: str | None = None,
                 db: Session = Depends(dbmod.get_db), user: User = Depends(require("inventory:read"))):
    return render(request, "inventario_movimientos.html", user,
                  movements=inventory.movements(db, product_id or None, warehouse_id or None),
                  lots=list(db.scalars(select(Lot).order_by(Lot.code))),
                  f={"product_id": product_id, "warehouse_id": warehouse_id}, **_catalogos(db))


@router.post("/inventario/movimientos", dependencies=[Depends(csrf_protect)])
async def ui_register(request: Request, db: Session = Depends(dbmod.get_db),
                      user: User = Depends(require("inventory:write"))):
    inventory.register(db, await form_dict(request), user.id)
    return back("/inventario/movimientos")


@router.post("/inventario/traspasos", dependencies=[Depends(csrf_protect)])
async def ui_transfer(request: Request, db: Session = Depends(dbmod.get_db),
                      user: User = Depends(require("inventory:write"))):
    inventory.transfer(db, await form_dict(request), user.id)
    return back("/inventario/movimientos")


@router.get("/inventario/lotes", response_class=HTMLResponse)
def ui_lots(request: Request, db: Session = Depends(dbmod.get_db),
            user: User = Depends(require("inventory:read"))):
    lots = [{"lot": lot, "kg": inventory.lot_balance(db, lot.id)}
            for lot in db.scalars(select(Lot).order_by(Lot.expires_on.is_(None), Lot.expires_on))]
    return render(request, "inventario_lotes.html", user, lots=lots,
                  expiring=inventory.expiring_lots(db), **_catalogos(db))


@router.post("/inventario/lotes", dependencies=[Depends(csrf_protect)])
async def ui_create_lot(request: Request, db: Session = Depends(dbmod.get_db),
                        user: User = Depends(require("inventory:write"))):
    inventory.create_lot(db, await form_dict(request), user.id)
    return back("/inventario/lotes")


@router.get("/inventario/productos", response_class=HTMLResponse)
def ui_products(request: Request, db: Session = Depends(dbmod.get_db),
                user: User = Depends(require("inventory:read"))):
    return render(request, "inventario_productos.html", user, totales=inventory.by_product(db),
                  **_catalogos(db))


@router.post("/inventario/productos", dependencies=[Depends(csrf_protect)])
async def ui_create_product(request: Request, db: Session = Depends(dbmod.get_db),
                            user: User = Depends(require("inventory:write"))):
    inventory.create_product(db, await form_dict(request), user.id)
    return back("/inventario/productos")


@router.post("/inventario/productos/{product_id}", dependencies=[Depends(csrf_protect)])
async def ui_update_product(product_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                            user: User = Depends(require("inventory:write"))):
    inventory.update_product(db, product_id, await form_dict(request), user.id)
    return back("/inventario/productos")


@router.get("/inventario/bodegas", response_class=HTMLResponse)
def ui_warehouses(request: Request, db: Session = Depends(dbmod.get_db),
                  user: User = Depends(require("inventory:read"))):
    rows = [{"warehouse": w, "kg": inventory.balance(db, warehouse_id=w.id)}
            for w in db.scalars(select(Warehouse).order_by(Warehouse.code))]
    return render(request, "inventario_bodegas.html", user, rows=rows)


@router.post("/inventario/bodegas", dependencies=[Depends(csrf_protect)])
async def ui_create_warehouse(request: Request, db: Session = Depends(dbmod.get_db),
                              user: User = Depends(require("inventory:write"))):
    inventory.create_warehouse(db, await form_dict(request), user.id)
    return back("/inventario/bodegas")


# ======================================================================= API REST (JSON)
@router.get("/api/inventario/existencias")
def api_stock(product_id: str | None = None, warehouse_id: str | None = None,
              db: Session = Depends(dbmod.get_db), user: User = Depends(require("inventory:read"))):
    rows = inventory.stock_rows(db, product_id, warehouse_id)
    return {"metricas": inventory.metrics(db), "existencias": [_fila(r) for r in rows]}


@router.get("/api/inventario/alertas")
def api_alerts(db: Session = Depends(dbmod.get_db), user: User = Depends(require("inventory:read"))):
    return {"bajo_minimo": [{"product_id": r["product"].id, "sku": r["product"].sku,
                             "producto": r["product"].name, "kg": r["kg"], "minimo_kg": r["min_kg"]}
                            for r in inventory.low_stock(db)],
            "por_caducar": [{"lot_id": r["lot"].id, "lote": r["lot"].code,
                             "producto": r["lot"].product.name, "kg": r["kg"],
                             "caduca": r["expires_on"].date().isoformat() if r["expires_on"] else None}
                            for r in inventory.expiring_lots(db)]}


@router.post("/api/inventario/movimientos", status_code=201)
async def api_register(request: Request, db: Session = Depends(dbmod.get_db),
                       user: User = Depends(require("inventory:write"))):
    mv = inventory.register(db, await request.json(), user.id)
    return JSONResponse({"movimiento": ser(mv),
                         "existencia_kg": inventory.balance(db, mv.product_id, mv.warehouse_id)},
                        status_code=201)


@router.post("/api/inventario/traspasos", status_code=201)
async def api_transfer(request: Request, db: Session = Depends(dbmod.get_db),
                       user: User = Depends(require("inventory:write"))):
    movs = inventory.transfer(db, await request.json(), user.id)
    return JSONResponse({"movimientos": ser(movs)}, status_code=201)
