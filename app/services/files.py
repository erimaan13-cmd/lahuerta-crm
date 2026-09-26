"""Adjuntos: escaneos y documentos. Solo se guardan (sin OCR, E-11) y se les puede poner vencimiento.

El archivo vive en disco (config.UPLOAD_DIR) y la fila en `attachments`; nunca se borra desde la
interfaz para no perder evidencia. Cada alta queda en la bitácora.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.audit import record
from app.models import Attachment
from app.services.common import DomainError, get_or_404

ENTITY_LABELS = {
    "asset": "Activo", "employee": "Empleado", "petty_cash": "Caja chica", "purchase_order": "Orden de compra",
    "sales_order": "Pedido", "lot": "Lote", "account": "Cuenta", "case": "Caso",
}
# Un documento hereda la reserva del módulo dueño: el comprobante de una caja es tan reservado como la
# caja, y la identificación de un empleado tanto como su expediente (regla 4c del proyecto y D-40).
# Antes bastaba `dashboard:read` para descargar cualquiera, que lo tienen los diez roles (D-59).
ENTITY_READ_PERMISSION = {
    "employee": "hr:read",
    "employment_contract": "hr:read",  # todavía no es un entity_type en uso; queda cubierto de antemano
    "petty_cash": "pettycash:read",
    "asset": "maintenance:read",
    "purchase_order": "procurement:read",
    "sales_order": "sales:read",
    "lot": "inventory:read",
    "account": "account:read",
    "case": "case:read",
}
# Un tipo que no esté en la tabla falla cerrado: solo administradores. Así, agregar un entity_type
# nuevo sin actualizar esta tabla deja el documento demasiado protegido, nunca demasiado expuesto.
UNKNOWN_ENTITY_PERMISSION = "audit:read"

KINDS = {
    "poliza_garantia": "Póliza de garantía", "factura_compra": "Factura de compra",
    "tarjeta_circulacion": "Tarjeta de circulación", "seguro": "Póliza de seguro",
    "verificacion": "Verificación", "manual": "Manual", "contrato": "Contrato",
    "identificacion": "Identificación", "comprobante": "Comprobante", "certificado": "Certificado",
    "otro": "Otro",
}


def permission_for(entity_type: str | None) -> str:
    """Permiso de lectura que exige un adjunto según a qué entidad pertenece."""
    return ENTITY_READ_PERMISSION.get(entity_type or "", UNKNOWN_ENTITY_PERMISSION)


def may_read(role: str | None, entity_type: str | None) -> bool:
    from app.permissions import has_permission
    return has_permission(role, permission_for(entity_type))


def parse_date(value: str | None) -> datetime | None:
    """Acepta AAAA-MM-DD (campo <input type=date>) y devuelve datetime a las 00:00."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10])
    except ValueError:
        raise DomainError(f"Fecha inválida: {value} (usa AAAA-MM-DD)")


def _dir() -> Path:
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return config.UPLOAD_DIR


def save_upload(db: Session, entity_type: str, entity_id: str, filename: str, content: bytes,
                actor_id: str | None, kind: str = "otro", title: str | None = None,
                expires_on: str | datetime | None = None, content_type: str | None = None) -> Attachment:
    if entity_type not in ENTITY_LABELS:
        raise DomainError(f"Tipo de registro no válido para adjuntos: {entity_type}")
    if not filename:
        raise DomainError("Selecciona un archivo")
    ext = Path(filename).suffix.lower()
    if ext not in config.UPLOAD_ALLOWED_EXT:
        raise DomainError(f"Tipo de archivo no permitido: {ext or 'sin extensión'}. "
                          f"Permitidos: {', '.join(sorted(config.UPLOAD_ALLOWED_EXT))}")
    if not content:
        raise DomainError("El archivo está vacío")
    if len(content) > config.UPLOAD_MAX_MB * 1024 * 1024:
        raise DomainError(f"El archivo pesa más de {config.UPLOAD_MAX_MB:g} MB")
    stored = f"{uuid.uuid4().hex}{ext}"
    (_dir() / stored).write_bytes(content)
    exp = expires_on if isinstance(expires_on, datetime) or expires_on is None else parse_date(expires_on)
    att = Attachment(entity_type=entity_type, entity_id=entity_id, kind=kind if kind in KINDS else "otro",
                     title=(title or Path(filename).stem)[:200], filename=filename[:255], stored_name=stored,
                     content_type=content_type, size_bytes=len(content), expires_on=exp, uploaded_by=actor_id)
    db.add(att)
    db.flush()
    record(db, actor_id, "adjunto.alta", entity_type, entity_id,
           after={"attachment_id": att.id, "titulo": att.title, "tipo": att.kind,
                  "archivo": att.filename, "vence": exp.date().isoformat() if exp else None},
           summary=f"Documento adjuntado: {att.title}")
    db.commit()
    return att


def for_entity(db: Session, entity_type: str, entity_id: str) -> list[Attachment]:
    return list(db.scalars(select(Attachment).where(Attachment.entity_type == entity_type,
                                                    Attachment.entity_id == entity_id)
                           .order_by(Attachment.uploaded_at.desc())))


def path_of(att: Attachment) -> Path:
    p = _dir() / att.stored_name
    if not p.exists():
        raise DomainError("El archivo ya no está disponible en el servidor")
    return p


def get(db: Session, attachment_id: str) -> Attachment:
    return get_or_404(db, Attachment, attachment_id, "Documento")


def expiring(db: Session, days: int | None = None) -> list[Attachment]:
    """Documentos con vencimiento dentro de N días (o ya vencidos)."""
    from datetime import timedelta

    from app.models import utcnow
    limit = utcnow() + timedelta(days=days if days is not None else config.DOC_EXPIRY_ALERT_DAYS)
    return list(db.scalars(select(Attachment).where(Attachment.expires_on.is_not(None),
                                                    Attachment.expires_on <= limit)
                           .order_by(Attachment.expires_on)))
