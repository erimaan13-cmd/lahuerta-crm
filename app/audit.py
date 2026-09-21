"""Bitácora de auditoría (RF-21, RNF-05, requisito de historial total — iteración 3).

Tres fuentes de eventos, todas en la misma tabla:
- negocio:   cada mutación de los servicios (crear, cambiar estado, convertir, fusionar…), con antes/después.
- acceso:    cada solicitud HTTP de un usuario autenticado (vistas, descargas, exportaciones, envíos),
             y los intentos rechazados (401/403/415/429) aunque no haya sesión.
- seguridad: inicios y cierres de sesión, fallos, bloqueos y gestión de usuarios.

Integridad: el ORM prohíbe UPDATE/DELETE sobre AuditEvent y cada evento guarda el hash del anterior
(cadena). verify_chain() detecta cualquier edición o borrado hecho directamente en la base.
"""
import hashlib
import itertools
import json
from contextvars import ContextVar
from datetime import datetime

from sqlalchemy import event, func, inspect as sa_inspect, select
from sqlalchemy.orm import Session

from app.models import AuditEvent

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
ip_var: ContextVar[str | None] = ContextVar("ip", default=None)

_order = itertools.count()
GENESIS = "0" * 64


def snapshot(obj) -> dict | None:
    if obj is None:
        return None
    out = {}
    for col in sa_inspect(obj).mapper.column_attrs:
        if col.key == "password_hash":
            continue
        v = getattr(obj, col.key)
        out[col.key] = v.isoformat() if isinstance(v, datetime) else v
    return out


def _actor_fields(db: Session, actor_id: str | None) -> dict:
    """Congela correo y rol del actor en el momento del evento (si luego cambian, el historial no se altera)."""
    if not actor_id:
        return {"actor_id": None, "actor_email": None, "actor_role": "sistema"}
    from app.models import User
    u = db.get(User, actor_id)
    return {"actor_id": actor_id, "actor_email": u.email if u else None, "actor_role": u.role if u else None}


def record(db: Session, actor_id: str | None, action: str, entity_type: str, entity_id: str | None,
           before: dict | None = None, after: dict | None = None, category: str = "negocio",
           summary: str | None = None, **extra) -> AuditEvent:
    ev = AuditEvent(action=action, entity_type=entity_type, entity_id=entity_id, before=before, after=after,
                    category=category, summary=summary, request_id=request_id_var.get(), ip=ip_var.get(),
                    **_actor_fields(db, actor_id), **extra)
    ev._order = next(_order)
    db.add(ev)
    return ev


def _payload(ev: AuditEvent) -> str:
    data = {k: getattr(ev, k) for k in ("seq", "at", "actor_id", "actor_email", "actor_role", "category", "action",
                                        "entity_type", "entity_id", "summary", "before", "after", "ip", "method",
                                        "path", "status", "request_id", "prev_hash")}
    data["at"] = ev.at.isoformat() if isinstance(ev.at, datetime) else str(ev.at)
    return json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)


def compute_hash(ev: AuditEvent) -> str:
    return hashlib.sha256(_payload(ev).encode()).hexdigest()


@event.listens_for(Session, "before_flush")
def _chain_new_events(session: Session, flush_context, instances):
    new = sorted((o for o in session.new if isinstance(o, AuditEvent) and o.seq is None),
                 key=lambda o: getattr(o, "_order", 0))
    if not new:
        return
    last = session.execute(select(AuditEvent.seq, AuditEvent.hash).order_by(AuditEvent.seq.desc()).limit(1)).first()
    seq, prev = (last[0], last[1]) if last and last[0] is not None else (0, GENESIS)
    for ev in new:
        seq += 1
        if ev.at is None:
            from app.models import utcnow
            ev.at = utcnow()
        ev.seq, ev.prev_hash = seq, prev
        ev.hash = compute_hash(ev)
        prev = ev.hash


@event.listens_for(AuditEvent, "before_update")
def _forbid_update(mapper, connection, target):
    raise PermissionError("La bitácora de auditoría es de solo inserción")


@event.listens_for(AuditEvent, "before_delete")
def _forbid_delete(mapper, connection, target):
    raise PermissionError("La bitácora de auditoría es de solo inserción")


def verify_chain(db: Session) -> dict:
    """Recalcula la cadena completa. Devuelve el primer evento alterado o faltante, si existe."""
    prev, expected_seq, n = GENESIS, 1, 0
    for ev in db.scalars(select(AuditEvent).order_by(AuditEvent.seq)
                         .execution_options(populate_existing=True)):  # lee siempre lo que hay en la BD
        n += 1
        if ev.seq != expected_seq:
            return {"ok": False, "checked": n, "broken_seq": expected_seq, "reason": "falta un evento (borrado)"}
        if ev.prev_hash != prev or compute_hash(ev) != ev.hash:
            return {"ok": False, "checked": n, "broken_seq": ev.seq, "reason": "contenido alterado"}
        prev, expected_seq = ev.hash, expected_seq + 1
    return {"ok": True, "checked": n, "broken_seq": None, "reason": None}


def count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(AuditEvent)) or 0
