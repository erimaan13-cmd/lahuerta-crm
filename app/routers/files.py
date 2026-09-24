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
from app.web import back, csrf_protect, render, require, ser

router = APIRouter(tags=["documentos"])


@router.post("/documentos", dependencies=[Depends(csrf_protect)])
async def ui_upload(request: Request, file: UploadFile = File(...), entity_type: str = Form(...),
                    entity_id: str = Form(...), kind: str = Form("otro"), title: str = Form(""),
                    expires_on: str = Form(""), next: str = Form("/"),
                    db: Session = Depends(dbmod.get_db), user: User = Depends(require("attachment:write"))):
    files_svc.save_upload(db, entity_type, entity_id, file.filename or "", await file.read(), user.id,
                          kind=kind, title=title or None, expires_on=expires_on or None,
                          content_type=file.content_type)
    return back(next or "/")


@router.get("/documentos/{attachment_id}")
def ui_download(attachment_id: str, db: Session = Depends(dbmod.get_db),
                user: User = Depends(require("dashboard:read"))):
    att = files_svc.get(db, attachment_id)
    return FileResponse(files_svc.path_of(att), filename=att.filename,
                        media_type=att.content_type or "application/octet-stream")


@router.get("/documentos")
def ui_list(request: Request, entity_type: str | None = None, db: Session = Depends(dbmod.get_db),
            user: User = Depends(require("dashboard:read"))):
    """Vencimientos próximos de todos los documentos (pólizas, seguros, verificaciones…)."""
    return render(request, "documentos.html", user, docs=files_svc.expiring(db, 3650),
                  soon=files_svc.expiring(db), kinds=files_svc.KINDS, entities=files_svc.ENTITY_LABELS)


@router.get("/api/documentos/{attachment_id}")
def api_attachment(attachment_id: str, db: Session = Depends(dbmod.get_db),
                   user: User = Depends(require("dashboard:read"))):
    return ser(files_svc.get(db, attachment_id))
