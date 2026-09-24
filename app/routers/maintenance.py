"""Mantenimiento: activos, planes de frecuencia y órdenes de trabajo.

La ficha del activo (`/mantenimiento/activos/{id}`) es la vista 360 que pidió el cliente: datos,
responsable, planes, órdenes, documentos escaneados e historial del registro.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import db as dbmod
from app.models import Asset, Employee, User
from app.services import files as files_svc, maintenance
from app.services.common import get_or_404
from app.web import back, csrf_protect, entity_history, form_dict, render, require, ser

router = APIRouter(tags=["mantenimiento"])


def _catalogos(db: Session) -> dict:
    """Listas para los formularios: a quién se asigna y qué etiquetas se muestran."""
    users = list(db.scalars(select(User).where(User.is_active.is_(True)).order_by(User.full_name)))
    employees = list(db.scalars(select(Employee).where(Employee.status == "activo").order_by(Employee.full_name)))
    return {"users": users, "employees": employees,
            # nombres por id: la lista de activos muestra a quién está asignado cada uno sin más consultas
            "names": {**{u.id: u.full_name for u in users}, **{e.id: e.full_name for e in employees}},
            "TYPES": maintenance.TYPES, "STATUSES": maintenance.STATUSES,
            "PLAN_KINDS": maintenance.PLAN_KINDS, "WO_KINDS": maintenance.WO_KINDS,
            "WO_STATUSES": maintenance.WO_STATUSES, "PROVIDERS": maintenance.PROVIDERS}


def _due(db: Session) -> dict:
    pendientes = maintenance.due_plans(db)
    return {"vencidos": [p for p in pendientes if p["estado"] == "vencido"],
            "proximos": [p for p in pendientes if p["estado"] == "proximo"]}


def _ser_due(rows: list[dict]) -> list[dict]:
    """Serializa los pendientes para la API (los objetos ORM no viajan en JSON)."""
    return [{"activo": r["asset"].code, "activo_id": r["asset"].id, "nombre_activo": r["asset"].name,
             "plan": r["plan"].name, "plan_id": r["plan"].id, "estado": r["estado"],
             "razones": r["razones"], "dias": r["dias"], "km_faltantes": r["km_faltantes"],
             "horas_faltantes": r["horas_faltantes"],
             "proximo_en": r["plan"].next_due_on.isoformat() if r["plan"].next_due_on else None,
             "proximo_km": r["plan"].next_due_km, "proximo_horas": r["plan"].next_due_hours}
            for r in rows]


# ------------------------------------------------------------------ interfaz
@router.get("/mantenimiento", response_class=HTMLResponse)
def ui_assets(request: Request, type: str | None = None, status: str | None = None,
              db: Session = Depends(dbmod.get_db), user: User = Depends(require("maintenance:read"))):
    return render(request, "mantenimiento.html", user, assets=maintenance.assets(db, type or None, status or None),
                  m=maintenance.metrics(db), f={"type": type, "status": status}, **_due(db), **_catalogos(db))


@router.post("/mantenimiento/activos", dependencies=[Depends(csrf_protect)])
async def ui_create_asset(request: Request, db: Session = Depends(dbmod.get_db),
                          user: User = Depends(require("maintenance:write"))):
    asset = maintenance.create_asset(db, await form_dict(request), user.id)
    return back(f"/mantenimiento/activos/{asset.id}")


@router.get("/mantenimiento/ordenes", response_class=HTMLResponse)
def ui_work_orders(request: Request, status: str | None = None, db: Session = Depends(dbmod.get_db),
                   user: User = Depends(require("maintenance:read"))):
    return render(request, "mantenimiento_ordenes.html", user,
                  orders=maintenance.work_orders(db, status or None), status=status,
                  assets=maintenance.assets(db), **_catalogos(db))


@router.get("/mantenimiento/activos/{asset_id}", response_class=HTMLResponse)
def ui_asset(asset_id: str, request: Request, db: Session = Depends(dbmod.get_db),
             user: User = Depends(require("maintenance:read"))):
    asset = get_or_404(db, Asset, asset_id, "Activo")
    return render(request, "mantenimiento_activo.html", user, **entity_history(db, user, asset.id), a=asset,
                  planes=[maintenance.plan_state(p, asset) for p in asset.plans],
                  orders=maintenance.work_orders(db, asset_id=asset.id),
                  assigned_user=db.get(User, asset.assigned_user_id) if asset.assigned_user_id else None,
                  assigned_employee=db.get(Employee, asset.assigned_employee_id) if asset.assigned_employee_id else None,
                  docs=files_svc.for_entity(db, "asset", asset.id), entity_type="asset", entity_id=asset.id,
                  next=f"/mantenimiento/activos/{asset.id}", **_catalogos(db))


@router.post("/mantenimiento/activos/{asset_id}/asignar", dependencies=[Depends(csrf_protect)])
async def ui_assign(asset_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                    user: User = Depends(require("maintenance:write"))):
    f = await form_dict(request)
    maintenance.assign(db, asset_id, user.id, f.get("assigned_user_id") or None,
                       f.get("assigned_employee_id") or None)
    return back(f"/mantenimiento/activos/{asset_id}")


@router.post("/mantenimiento/activos/{asset_id}/odometro", dependencies=[Depends(csrf_protect)])
async def ui_odometer(asset_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                      user: User = Depends(require("maintenance:write"))):
    """Captura de kilometraje u horas desde el patio: es el dato que dispara los vencimientos."""
    f = await form_dict(request)
    maintenance.update_asset(db, asset_id, {"odometer_km": f.get("odometer_km") or None,
                                            "hours_used": f.get("hours_used") or None}, user.id)
    return back(f"/mantenimiento/activos/{asset_id}")


@router.post("/mantenimiento/activos/{asset_id}/estado", dependencies=[Depends(csrf_protect)])
async def ui_asset_status(asset_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                          user: User = Depends(require("maintenance:write"))):
    f = await form_dict(request)
    maintenance.set_status(db, asset_id, f.get("status") or "", user.id)
    return back(f"/mantenimiento/activos/{asset_id}")


@router.post("/mantenimiento/activos/{asset_id}/planes", dependencies=[Depends(csrf_protect)])
async def ui_create_plan(asset_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                         user: User = Depends(require("maintenance:write"))):
    maintenance.create_plan(db, asset_id, await form_dict(request), user.id)
    return back(f"/mantenimiento/activos/{asset_id}")


@router.post("/mantenimiento/ordenes", dependencies=[Depends(csrf_protect)])
async def ui_create_wo(request: Request, db: Session = Depends(dbmod.get_db),
                       user: User = Depends(require("maintenance:write"))):
    f = await form_dict(request)
    wo = maintenance.create_work_order(db, f, user.id)
    return back(f.get("next") or f"/mantenimiento/activos/{wo.asset_id}")


@router.post("/mantenimiento/ordenes/{wo_id}/cerrar", dependencies=[Depends(csrf_protect)])
async def ui_close_wo(wo_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                      user: User = Depends(require("maintenance:write"))):
    f = await form_dict(request)
    wo = maintenance.close_work_order(db, wo_id, f, user.id)
    return back(f.get("next") or f"/mantenimiento/activos/{wo.asset_id}")


# ------------------------------------------------------------------ API REST
@router.get("/api/mantenimiento/activos")
def api_assets(type: str | None = None, status: str | None = None, db: Session = Depends(dbmod.get_db),
               user: User = Depends(require("maintenance:read"))):
    return ser(maintenance.assets(db, type, status))


@router.post("/api/mantenimiento/activos", status_code=201)
async def api_create_asset(request: Request, db: Session = Depends(dbmod.get_db),
                           user: User = Depends(require("maintenance:write"))):
    return ser(maintenance.create_asset(db, await request.json(), user.id))


@router.get("/api/mantenimiento/pendientes")
def api_due(db: Session = Depends(dbmod.get_db), user: User = Depends(require("maintenance:read"))):
    pendientes = maintenance.due_plans(db)
    return {"vencidos": _ser_due([p for p in pendientes if p["estado"] == "vencido"]),
            "proximos": _ser_due([p for p in pendientes if p["estado"] == "proximo"]),
            "metricas": maintenance.metrics(db)}


@router.post("/api/mantenimiento/ordenes/{wo_id}/cerrar")
async def api_close_wo(wo_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                       user: User = Depends(require("maintenance:write"))):
    wo = maintenance.close_work_order(db, wo_id, await request.json(), user.id)
    plan = wo.plan
    return {"orden": ser(wo), "activo": ser(wo.asset),
            "plan": {**ser(plan), "estado": maintenance.plan_state(plan, wo.asset)["estado"]} if plan else None}
