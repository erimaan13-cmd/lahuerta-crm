import re

from app import config
from app.textutil import norm_text, strip_accents  # noqa: F401  (re-export)


class DomainError(Exception):
    """Regla de negocio violada → HTTP 422."""
    status_code = 422

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFound(DomainError):
    status_code = 404


def norm_email(email: str | None) -> str | None:
    if not email:
        return None
    email = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", email):
        raise DomainError(f"Correo inválido: {email}")
    return email


def norm_phone(phone: str | None) -> str | None:
    """Normaliza a 10 dígitos nacionales (México) cuando es posible."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 12 and digits.startswith("52"):
        digits = digits[2:]
    elif len(digits) == 13 and digits.startswith("521"):
        digits = digits[3:]
    if len(digits) < 8:
        raise DomainError(f"Teléfono inválido: {phone}")
    return digits


def email_domain(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    d = email.split("@", 1)[1].lower()
    return None if d in config.PUBLIC_EMAIL_DOMAINS else d


def get_or_404(db, model, id_: str, label: str):
    obj = db.get(model, id_)
    if obj is None:
        raise NotFound(f"No se encontró {label}: {id_}")
    return obj
