"""Capa de integración de correo (EMAIL PROVIDER → INGESTA). Todos los proveedores son de SOLO LECTURA:
ninguno envía, borra, archiva ni modifica buzones (regla 11 del encargo)."""
import email
import email.policy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path
from typing import Protocol


@dataclass
class RawEmail:
    provider: str
    message_id: str
    from_email: str
    subject: str
    body: str
    from_name: str | None = None
    to: str | None = None
    thread_id: str | None = None
    received_at: datetime | None = None
    has_attachments: bool = False
    raw_hash: str | None = None
    is_demo: bool = False


class EmailProvider(Protocol):
    name: str

    def fetch(self) -> list[RawEmail]: ...


def _naive_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def parse_eml_bytes(data: bytes, provider: str = "eml") -> RawEmail:
    msg = email.message_from_bytes(data, policy=email.policy.default)
    name, addr = parseaddr(str(msg.get("From", "")))
    body_part = msg.get_body(preferencelist=("plain", "html"))
    body = body_part.get_content() if body_part else ""
    has_att = any(True for _ in msg.iter_attachments())
    digest = hashlib.sha256(data).hexdigest()
    try:
        received = parsedate_to_datetime(msg["Date"]) if msg["Date"] else None
    except (TypeError, ValueError):
        received = None
    return RawEmail(provider=provider, message_id=(msg.get("Message-ID") or f"<sha256-{digest[:32]}>").strip(),
                    from_email=addr.lower(), from_name=name or None, to=str(msg.get("To", "")) or None,
                    subject=str(msg.get("Subject", "")), body=body,
                    thread_id=(msg.get("In-Reply-To") or msg.get("Message-ID")),
                    received_at=_naive_utc(received), has_attachments=has_att, raw_hash=digest,
                    is_demo=str(msg.get("X-Demo-Data", "")).lower() == "true")


class EmlDirectoryProvider:
    """Lee archivos .eml de una carpeta (exportaciones reales o datos de prueba)."""
    name = "eml"

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    def fetch(self) -> list[RawEmail]:
        return [parse_eml_bytes(p.read_bytes(), self.name) for p in sorted(self.directory.glob("*.eml"))]


class MockMailboxProvider:
    """Buzón simulado a partir de un JSON de correos sintéticos."""
    name = "mock"

    def __init__(self, json_path: str | Path):
        self.json_path = Path(json_path)

    def fetch(self) -> list[RawEmail]:
        items = json.loads(self.json_path.read_text(encoding="utf-8"))
        out = []
        for it in items:
            out.append(RawEmail(provider=self.name, message_id=it["message_id"], from_email=it["from_email"].lower(),
                                from_name=it.get("from_name"), to=it.get("to", "administracion@demo.local"),
                                subject=it["subject"], body=it["body"],
                                received_at=datetime.fromisoformat(it["received_at"]) if it.get("received_at") else None,
                                has_attachments=it.get("has_attachments", False), is_demo=True))
        return out


class GmailProvider:
    """P1 (RF-30): Gmail API con alcance `gmail.readonly` y OAuth de la cuenta de La Huerta.
    No implementado en el MVP: no hay autorización sobre el buzón real."""
    name = "gmail"

    def __init__(self, *_, **__):
        raise NotImplementedError("GmailProvider es P1: requiere OAuth autorizado por La Huerta (solo lectura)")
