"""Avisos internos (E-12): pantalla única con lo que está por vencer o ya venció.

Ver un aviso solo pide `notification:read`; generarlos pide `integration:run`, porque generar recorre
todos los módulos y equivale a correr un proceso del sistema.

El envío por correo NO ocurre aquí: mientras no haya adaptador configurado, los avisos quedan en cola
con estado "sin_adaptador" (regla 3 del proyecto). La pantalla lo dice con todas sus letras.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app import config, db as dbmod
from app.models import User
from app.services import notifications as avisos
from app.web import back, csrf_protect, form_dict, render, require, ser

router = APIRouter(tags=["avisos"])


# ======================================================================= interfaz
@router.get("/avisos", response_class=HTMLResponse)
def ui_notifications(request: Request, status: str = "pendiente", kind: str | None = None,
                     db: Session = Depends(dbmod.get_db), user: User = Depends(require("notification:read"))):
    return render(request, "avisos.html", user,
                  avisos=avisos.listing(db, user, status or None, kind or None),
                  m=avisos.metrics(db), kinds=avisos.KIND_LABELS, correo_activo=config.NOTIFY_EMAIL_ENABLED,
                  f={"status": status, "kind": kind})


@router.post("/avisos/{notification_id}/leido", dependencies=[Depends(csrf_protect)])
async def ui_mark_read(notification_id: str, request: Request, db: Session = Depends(dbmod.get_db),
                       user: User = Depends(require("notification:read"))):
    avisos.mark_read(db, notification_id, user.id)
    f = await form_dict(request)
    return back(f.get("next") or "/avisos")


@router.post("/avisos/silenciar", dependencies=[Depends(csrf_protect)])
async def ui_mute(request: Request, db: Session = Depends(dbmod.get_db),
                  user: User = Depends(require("notification:read"))):
    """Silenciar es una decisión del área, no del administrador: basta con poder ver los avisos."""
    f = await form_dict(request)
    dias = f.get("days")
    avisos.mute(db, f.get("mute_key") or "", int(dias) if dias else None, user.id, f.get("reason"))
    return back(f.get("next") or "/avisos")


@router.post("/avisos/reactivar", dependencies=[Depends(csrf_protect)])
async def ui_unmute(request: Request, db: Session = Depends(dbmod.get_db),
                    user: User = Depends(require("notification:read"))):
    f = await form_dict(request)
    avisos.unmute(db, f.get("mute_key") or "", user.id)
    return back(f.get("next") or "/avisos")


@router.post("/avisos/generar", dependencies=[Depends(csrf_protect)])
def ui_generate(db: Session = Depends(dbmod.get_db), user: User = Depends(require("integration:run"))):
    avisos.generate(db, user.id)
    return back("/avisos")


# ======================================================================= API
@router.get("/api/avisos")
def api_notifications(status: str = "pendiente", kind: str | None = None, db: Session = Depends(dbmod.get_db),
                      user: User = Depends(require("notification:read"))):
    return ser(avisos.listing(db, user, status or None, kind or None))


@router.post("/api/avisos/generar")
def api_generate(db: Session = Depends(dbmod.get_db), user: User = Depends(require("integration:run"))):
    return avisos.generate(db, user.id)


@router.post("/api/avisos/{notification_id}/leido")
def api_mark_read(notification_id: str, db: Session = Depends(dbmod.get_db),
                  user: User = Depends(require("notification:read"))):
    return {"aviso": ser(avisos.mark_read(db, notification_id, user.id))}


@router.get("/api/avisos/pendientes")
def api_pending(db: Session = Depends(dbmod.get_db), user: User = Depends(require("notification:read"))):
    """Conteo para la insignia del menú (la barra lo pide con una llamada ligera)."""
    return {"pendientes": avisos.pending_count(db, user)}
