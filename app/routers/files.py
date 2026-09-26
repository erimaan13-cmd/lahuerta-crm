"""Adjuntos: una sola ruta para subir y otra para descargar, usadas por todos los módulos.

Los documentos escaneados se guardan tal cual (sin OCR, E-11). Si el documento tiene vencimiento,
el módulo de avisos lo recoge solo.
"""
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import db as dbmod
from app.models import User
from app.services import files as files_svc
from app.web import Forbidden, back, csrf_protect, render, require, ser

router = APIRouter(tags=["documentos"])


@router.post("/documentos", dependencies=[Depends(csrf_protect)])
async def ui_upload(request: Request, file: UploadFile = File(...), entity_type: str = Form(...),
                    entity_id: str = Form(...), kind: str = Form("otro"), title: str = Form(""),
                    expires_on: str = Form(""), next: str = Form("/"),
                    db: Session = Depends(dbmod.get_db), user: User = Depends(require("attachment:write"))):
    # Un documento plantado en el expediente de otra área se lee como si lo hubiera puesto esa área:
    # subir exige el permiso de escritura del módulo dueño, no solo poder subir archivos (D-61).
    if not files_svc.may_write(user.role, entity_type):
        raise Forbidden(files_svc.write_permission_for(entity_type))
    files_svc.save_upload(db, entity_type, entity_id, file.filename or "", await file.read(), user.id,
                          kind=kind, title=title or None, expires_on=expires_on or None,
                          content_type=file.content_type)
    return back(next or "/")


def _guard(user: User, att) -> None:
    """Un adjunto solo se entrega a quien puede leer el módulo dueño (regla 4c, D-40, D-59)."""
    if not files_svc.may_read(user.role, att.entity_type):
        raise Forbidden(files_svc.permission_for(att.entity_type))


@router.get("/documentos/{attachment_id}")
def ui_download(attachment_id: str, db: Session = Depends(dbmod.get_db),
                user: User = Depends(require("dashboard:read"))):
    att = files_svc.get(db, attachment_id)
    _guard(user, att)
    return FileResponse(files_svc.path_of(att), filename=att.filename,
                        media_type=att.content_type or "application/octet-stream")


@router.get("/documentos")
def ui_list(request: Request, entity_type: str | None = None, db: Session = Depends(dbmod.get_db),
            user: User = Depends(require("dashboard:read"))):
    """Vencimientos próximos de los documentos que este usuario puede leer.

    Pedir explícitamente un tipo reservado (`?entity_type=employee` sin `hr:read`) da 403; sin filtro,
    la lista se recorta a lo permitido para que la pestaña siga sirviendo a los demás roles.
    """
    if entity_type and not files_svc.may_read(user.role, entity_type):
        raise Forbidden(files_svc.permission_for(entity_type))
    visible = [a for a in files_svc.expiring(db, 3650) if files_svc.may_read(user.role, a.entity_type)]
    soon = [a for a in files_svc.expiring(db) if files_svc.may_read(user.role, a.entity_type)]
    if entity_type:
        visible = [a for a in visible if a.entity_type == entity_type]
        soon = [a for a in soon if a.entity_type == entity_type]
    return render(request, "documentos.html", user, docs=visible, soon=soon,
                  kinds=files_svc.KINDS, entities=files_svc.ENTITY_LABELS)


@router.get("/api/documentos/{attachment_id}")
def api_attachment(attachment_id: str, db: Session = Depends(dbmod.get_db),
                   user: User = Depends(require("dashboard:read"))):
    att = files_svc.get(db, attachment_id)
    _guard(user, att)
    return ser(att)
