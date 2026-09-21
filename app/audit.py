"""Bitácora de auditoría (RF-21, RNF-05)."""
from contextvars import ContextVar
from datetime import datetime

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.models import AuditEvent

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


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


def record(db: Session, actor_id: str | None, action: str, entity_type: str,
           entity_id: str | None, before: dict | None = None, after: dict | None = None) -> None:
    db.add(AuditEvent(actor_id=actor_id, action=action, entity_type=entity_type,
                      entity_id=entity_id, before=before, after=after,
                      request_id=request_id_var.get()))
