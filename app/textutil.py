"""Utilidades de texto puras (sin dependencias del dominio), compartidas por servicios y clasificador."""
import re
import unicodedata


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(c))


def norm_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", strip_accents(text or "").lower()).strip()
