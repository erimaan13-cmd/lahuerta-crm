"""Normalización de correos: HTML → texto, quitar historial citado, texto para reglas."""
import html
import re

from app.textutil import norm_text

_QUOTE_MARKERS = [
    r"^\s*el .{3,120} escribi[oó]:\s*$",
    r"^\s*on .{3,120} wrote:\s*$",
    r"^\s*-{2,}\s*(mensaje original|original message)\s*-{2,}",
    r"^\s*de:\s.+$",
    r"^\s*from:\s.+$",
]


def html_to_text(raw: str) -> str:
    if "<" not in raw:
        return raw
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    t = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(t)


def strip_quoted(text: str) -> str:
    out = []
    for line in text.splitlines():
        low = line.strip().lower()
        if any(re.match(p, low) for p in _QUOTE_MARKERS):
            break
        if low.startswith(">"):
            continue
        out.append(line)
    return "\n".join(out).strip()


def clean_body(raw: str) -> str:
    text = strip_quoted(html_to_text(raw or ""))
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def rules_text(subject: str, body_clean: str) -> str:
    return norm_text(f"{subject}\n{body_clean}")
