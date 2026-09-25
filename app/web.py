"""Piezas compartidas por todas las rutas (plantillas, sesión, permisos, CSRF).

Viven aquí —y no en `main.py`— para que cada módulo de `app/routers/` las use sin importar la
aplicación y sin crear importaciones circulares.
"""
from __future__ import annotations

import hmac
from pathlib import Path

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config, db as dbmod
from app.audit import snapshot
from app.classifier.taxonomy import CATEGORIES
from app.models import AuditEvent, User, utcnow
from app.permissions import ROLE_LABELS, has_permission
from app.security import read_session_token
from app.services import crm, pipeline
from app.services.files import KINDS as ATTACHMENT_KINDS
from app.services.business_time import to_local

BASE = Path(__file__).resolve().parent
CSRF_COOKIE = "crm_csrf"

templates = Jinja2Templates(directory=str(BASE / "templates"))


def _local(dt, fmt="%d/%m/%Y %H:%M"):
    return to_local(dt).strftime(fmt) if dt else "—"


def _money(v):
    return "—" if v in (None, "") else f"${float(v):,.2f}"


def _kg(v):
    return "—" if v in (None, "") else f"{float(v):,.2f} kg"


# Códigos internos que se muestran en pantalla. El diccionario cubre los que no se
# entienden solos; el resto se convierte con la regla general (guion bajo → espacio,
# mayúscula inicial), para que nadie lea "cliente_recurrente" en la interfaz.
ROTULOS = {
    "needs_review": "Por revisar", "auto": "Automático", "confirmado": "Confirmado",
    "corregido": "Corregido", "aplicado": "Aplicado", "sin_adaptador": "En cola (sin correo)",
    "atencion": "Atención a clientes", "administracion": "Administración",
    "auto_lead": "Alta de lead", "auto_email": "Correo clasificado", "manual": "Creada a mano",
    "cliente_activo": "Cliente activo", "cliente_recurrente": "Cliente recurrente",
    # "Prospecto" es la persona que preguntó (pestaña Prospectos); una CUENTA que aún no
    # compra es un "Cliente potencial". Así los cuatro estados de cuenta se leen en
    # positivo y nadie confunde a la persona con la empresa (D-56).
    "prospecto": "Cliente potencial",
    "lead": "Prospecto", "account": "Cuenta", "contact": "Contacto",
    "opportunity": "Oportunidad", "quote": "Cotización", "case": "Caso",
    "crear_lead": "Crear prospecto", "crear_tarea": "Crear tarea", "abrir_caso": "Abrir caso",
    "registrar_actividad": "Registrar actividad", "reenviar_fuera_crm": "Reenviar fuera del sistema",
    "ignorar": "Ignorar", "revisar": "Revisar a mano",
}


def _rotulo(v) -> str:
    if v in (None, ""):
        return "—"
    s = str(v)
    return ROTULOS.get(s) or (s.replace("_", " ").capitalize())


def _expiry(dt, warn_days: int = 30) -> str:
    """Clase visual de un vencimiento: rojo si ya pasó, ámbar si está cerca."""
    if not dt:
        return ""
    days = (dt - utcnow()).days
    return "bad" if days < 0 else ("warn" if days <= warn_days else "ok")


templates.env.filters["local"] = _local
templates.env.filters["expiry"] = _expiry
templates.env.filters["money"] = _money
templates.env.filters["kg"] = _kg
templates.env.filters["rotulo"] = _rotulo
templates.env.globals.update(STAGE_LABELS=pipeline.STAGE_LABELS, CATEGORIES=CATEGORIES,
                             ROLE_LABELS=ROLE_LABELS, has_permission=has_permission,
                             QUOTE_TRANSITIONS=crm.QUOTE_TRANSITIONS, KINDS=ATTACHMENT_KINDS,
                             now=utcnow)


class NotAuthenticated(Exception):
    pass


class Forbidden(Exception):
    def __init__(self, perm):
        self.perm = perm


class CsrfError(Exception):
    pass


async def csrf_protect(request: Request):
    """Doble envío: el token del formulario debe coincidir con la cookie (RNF-01)."""
    form = await request.form()
    sent, cookie = form.get("csrf_token"), request.cookies.get(CSRF_COOKIE)
    if not sent or not cookie or not hmac.compare_digest(str(sent), cookie):
        raise CsrfError()


def current_user(request: Request, db: Session = Depends(dbmod.get_db)) -> User:
    uid = read_session_token(request.cookies.get(config.SESSION_COOKIE))
    user = db.get(User, uid) if uid else None
    if not user or not user.is_active:
        raise NotAuthenticated()
    return user


def require(perm: str):
    def dep(user: User = Depends(current_user)) -> User:
        if not has_permission(user.role, perm):
            raise Forbidden(perm)
        return user
    return dep


def entity_history(db: Session, user: User, entity_id: str) -> dict:
    """Historial del registro (solo si el usuario puede ver la bitácora)."""
    if not has_permission(user.role, "audit:read"):
        return {}
    evs = list(db.scalars(select(AuditEvent).where(AuditEvent.entity_id == entity_id)
                          .order_by(AuditEvent.seq.desc()).limit(200)))
    return {"history": evs, "history_id": entity_id}


def render(request, name, user, **ctx):
    return templates.TemplateResponse(request, name, {"user": user, **ctx})


def back(url: str):
    return RedirectResponse(url, status_code=303)


async def form_dict(request: Request) -> dict:
    return {k: v for k, v in (await request.form()).items()}


def ser(obj):
    if isinstance(obj, list):
        return [ser(o) for o in obj]
    return snapshot(obj)
