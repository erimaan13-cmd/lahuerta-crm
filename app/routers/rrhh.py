"""Recursos Humanos: expedientes, puestos y contratos.

Todo aquí exige los permisos hr:read / hr:write, que solo tienen los roles "rrhh" y "admin": son
datos personales (E-08). Las rutas no deciden nada, solo validan permiso y delegan en app/services/hr.py.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app import config, db as dbmod
from app.models import Employee, User
from app.services import files as files_svc, hr
from app.services.common import get_or_404
from app.web import back, csrf_protect, entity_history, form_dict, render, require, ser

router = APIRouter(tags=["rrhh"])


# ======================================================================= interfaz
@router.get("/rrhh", response_class=HTMLResponse)
def ui_rrhh(request: Request, area: str | None = None, status: str | None = None,
            db: Session = Depends(dbmod.get_db), user: User = Depends(require("hr:read"))):
    return render(request, "rrhh.html", user, empleados=hr.employees(db, area or None, status or None),
                  m=hr.metrics(db), vencen=hr.contracts_expiring(db), areas=hr.areas(db),
                  puestos=hr.job_profiles(db), estados=hr.EMPLOYEE_STATUS,
                  alerta_dias=config.CONTRACT_ALERT_DAYS, f={"area": area, "status": status})


@router.get("/rrhh/puestos", response_class=HTMLResponse)
def ui_job_profiles(request: Request, db: Session = Depends(dbmod.get_db),
                    user: User = Depends(require("hr:read"))):
    return render(request, "puestos.html", user, puestos=hr.job_profiles(db), bullets=hr.bullets)


@router.post("/rrhh/puestos", dependencies=[Depends(csrf_protect)])
async def ui_create_job_profile(request: Request, db: Session = Depends(dbmod.get_db),
                                user: User = Depends(require("hr:write"))):
    hr.create_job_profile(db, await form_dict(request), user.id)
    return back("/rrhh/puestos")


@router.get("/rrhh/empleados/{employee_id}", response_class=HTMLResponse)
def ui_employee(employee_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                user: User = Depends(require("hr:read"))):
    e = get_or_404(db, Employee, employee_id, "Empleado")
    return render(request, "empleado.html", user, **entity_history(db, user, e.id), e=e,
                  contratos=sorted(e.contracts, key=lambda c: c.start_on, reverse=True),
                  vigente=hr.current_contract(db, e.id), puestos=hr.job_profiles(db),
                  tipos=hr.CONTRACT_TYPES, estados_contrato=hr.CONTRACT_STATUS, bullets=hr.bullets,
                  docs=files_svc.for_entity(db, "employee", e.id))


@router.post("/rrhh/empleados", dependencies=[Depends(csrf_protect)])
async def ui_create_employee(request: Request, db: Session = Depends(dbmod.get_db),
                             user: User = Depends(require("hr:write"))):
    e = hr.create_employee(db, await form_dict(request), user.id)
    return back(f"/rrhh/empleados/{e.id}")


@router.post("/rrhh/empleados/{employee_id}/actualizar", dependencies=[Depends(csrf_protect)])
async def ui_update_employee(employee_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                             user: User = Depends(require("hr:write"))):
    hr.update_employee(db, employee_id, await form_dict(request), user.id)
    return back(f"/rrhh/empleados/{employee_id}")


@router.post("/rrhh/empleados/{employee_id}/baja", dependencies=[Depends(csrf_protect)])
async def ui_terminate(employee_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                       user: User = Depends(require("hr:write"))):
    f = await form_dict(request)
    hr.terminate(db, employee_id, f.get("fecha") or f.get("end_on"), f.get("motivo") or f.get("reason"), user.id)
    return back(f"/rrhh/empleados/{employee_id}")


@router.post("/rrhh/empleados/{employee_id}/contratos", dependencies=[Depends(csrf_protect)])
async def ui_add_contract(employee_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                          user: User = Depends(require("hr:write"))):
    hr.add_contract(db, employee_id, await form_dict(request), user.id)
    return back(f"/rrhh/empleados/{employee_id}")


@router.post("/rrhh/contratos/{contract_id}/renovar", dependencies=[Depends(csrf_protect)])
async def ui_renew_contract(contract_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                            user: User = Depends(require("hr:write"))):
    nuevo = hr.renew_contract(db, contract_id, await form_dict(request), user.id)
    return back(f"/rrhh/empleados/{nuevo.employee_id}")


@router.post("/rrhh/contratos/{contract_id}/terminar", dependencies=[Depends(csrf_protect)])
async def ui_end_contract(contract_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                          user: User = Depends(require("hr:write"))):
    c = hr.end_contract(db, contract_id, await form_dict(request), user.id)
    return back(f"/rrhh/empleados/{c.employee_id}")


# ======================================================================= API
@router.get("/api/rrhh/empleados")
def api_employees(area: str | None = None, status: str | None = None, db: Session = Depends(dbmod.get_db),
                  user: User = Depends(require("hr:read"))):
    return ser(hr.employees(db, area, status))


@router.post("/api/rrhh/empleados", status_code=201)
async def api_create_employee(request: Request, db: Session = Depends(dbmod.get_db),
                              user: User = Depends(require("hr:write"))):
    return {"employee": ser(hr.create_employee(db, await request.json(), user.id))}


@router.get("/api/rrhh/contratos-por-vencer")
def api_contracts_expiring(days: int | None = None, db: Session = Depends(dbmod.get_db),
                           user: User = Depends(require("hr:read"))):
    return [{**ser(c), "empleado": c.employee.full_name, "area": c.employee.area}
            for c in hr.contracts_expiring(db, days)]
