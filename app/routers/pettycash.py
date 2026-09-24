"""Caja chica: cajas asignadas, gastos con comprobante y reposiciones del fondo fijo (E-09).

El comprobante se sube primero con el servicio de adjuntos y su identificador se le pasa al servicio;
así un gasto nunca queda guardado sin su respaldo.
"""
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import db as dbmod
from app.models import PettyCashFund, User
from app.services import files as files_svc, pettycash as caja
from app.services.common import get_or_404
from app.web import back, csrf_protect, entity_history, form_dict, render, require, ser

router = APIRouter(tags=["caja chica"])


def _responsables(db: Session) -> list[User]:
    return list(db.scalars(select(User).where(User.is_active.is_(True)).order_by(User.full_name)))


# ======================================================================= interfaz
@router.get("/caja", response_class=HTMLResponse)
def ui_funds(request: Request, db: Session = Depends(dbmod.get_db),
             user: User = Depends(require("pettycash:read"))):
    cajas = [{"f": f, "saldo": caja.balance(db, f.id),
              "responsable": db.get(User, f.responsible_user_id) if f.responsible_user_id else None}
             for f in caja.funds(db)]
    return render(request, "caja.html", user, cajas=cajas, m=caja.metrics(db), usuarios=_responsables(db))


@router.get("/caja/{fund_id}.csv")
def ui_fund_csv(fund_id: str, desde: str | None = None, hasta: str | None = None,
                db: Session = Depends(dbmod.get_db), user: User = Depends(require("pettycash:read"))):
    """Exportación para el contador. BOM al inicio para que Excel respete los acentos."""
    f = get_or_404(db, PettyCashFund, fund_id, "Caja chica")
    cuerpo = caja.export_csv(db, f.id, desde, hasta)
    nombre = f"caja_{f.name.lower().replace(' ', '_')}.csv"
    return Response("﻿" + cuerpo, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"'})


@router.get("/caja/{fund_id}", response_class=HTMLResponse)
def ui_fund(fund_id: str, request: Request, desde: str | None = None, hasta: str | None = None,
            db: Session = Depends(dbmod.get_db), user: User = Depends(require("pettycash:read"))):
    f = get_or_404(db, PettyCashFund, fund_id, "Caja chica")
    movs = caja.entries(db, f.id, desde or None, hasta or None)
    return render(request, "caja_detalle.html", user, **entity_history(db, user, f.id), f=f, movs=movs,
                  saldo=caja.balance(db, f.id), categorias=caja.CATEGORIES, tipos=caja.TYPES,
                  usuarios=_responsables(db), docs=files_svc.for_entity(db, "petty_cash", f.id),
                  filtro={"desde": desde, "hasta": hasta})


@router.post("/caja", dependencies=[Depends(csrf_protect)])
async def ui_create_fund(request: Request, db: Session = Depends(dbmod.get_db),
                         user: User = Depends(require("pettycash:write"))):
    f = caja.create_fund(db, await form_dict(request), user.id)
    return back(f"/caja/{f.id}")


@router.post("/caja/{fund_id}/gastos", dependencies=[Depends(csrf_protect)])
async def ui_add_expense(fund_id: str, request: Request, file: UploadFile | None = File(None),
                         amount_mxn: str = Form(""), category: str = Form("otro"),
                         description: str = Form(""), at: str = Form(""),
                         db: Session = Depends(dbmod.get_db),
                         user: User = Depends(require("pettycash:write"))):
    """El archivo se guarda primero; si el servicio rechaza el gasto, el comprobante queda como
    documento de la caja (nunca se pierde evidencia) y el gasto no se registra."""
    recibo = None
    if file is not None and file.filename:
        recibo = files_svc.save_upload(db, "petty_cash", fund_id, file.filename, await file.read(), user.id,
                                       kind="comprobante", title=description or file.filename,
                                       content_type=file.content_type).id
    caja.add_expense(db, fund_id, {"amount_mxn": amount_mxn, "category": category,
                                   "description": description, "at": at or None}, user.id, receipt_id=recibo)
    return back(f"/caja/{fund_id}")


@router.post("/caja/{fund_id}/reposiciones", dependencies=[Depends(csrf_protect)])
async def ui_add_replenishment(fund_id: str, request: Request, file: UploadFile | None = File(None),
                               amount_mxn: str = Form(""), description: str = Form(""), at: str = Form(""),
                               db: Session = Depends(dbmod.get_db),
                               user: User = Depends(require("pettycash:write"))):
    recibo = None
    if file is not None and file.filename:
        recibo = files_svc.save_upload(db, "petty_cash", fund_id, file.filename, await file.read(), user.id,
                                       kind="comprobante", title=description or file.filename,
                                       content_type=file.content_type).id
    caja.add_replenishment(db, fund_id, {"amount_mxn": amount_mxn, "description": description,
                                         "at": at or None}, user.id, receipt_id=recibo)
    return back(f"/caja/{fund_id}")


# ======================================================================= API
@router.get("/api/caja")
def api_funds(db: Session = Depends(dbmod.get_db), user: User = Depends(require("pettycash:read"))):
    return [{**ser(f), "saldo_mxn": caja.balance(db, f.id)} for f in caja.funds(db)]


@router.get("/api/caja/{fund_id}/saldo")
def api_balance(fund_id: str, db: Session = Depends(dbmod.get_db),
                user: User = Depends(require("pettycash:read"))):
    f = get_or_404(db, PettyCashFund, fund_id, "Caja chica")
    return {"caja": f.name, "fondo_mxn": f.fund_amount_mxn, "saldo_mxn": caja.balance(db, f.id)}


@router.post("/api/caja/{fund_id}/reposiciones", status_code=201)
async def api_add_replenishment(fund_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                                user: User = Depends(require("pettycash:write"))):
    data = await request.json()
    e = caja.add_replenishment(db, fund_id, data, user.id, receipt_id=data.get("receipt_id"))
    return {"movimiento": ser(e), "saldo_mxn": caja.balance(db, fund_id)}
