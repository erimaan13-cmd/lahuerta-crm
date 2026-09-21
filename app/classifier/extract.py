"""Extracción de entidades desde el correo (RF-13). Funciones puras; el catálogo de productos
se inyecta como parámetro para no depender de la base de datos."""
import re
from dataclasses import dataclass

from app.textutil import norm_text

PUBLIC_DOMAINS = {"gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "yahoo.com.mx", "live.com",
                  "live.com.mx", "icloud.com", "prodigy.net.mx", "hotmail.es", "outlook.es", "msn.com"}

CITIES = {
    "monterrey": ("Monterrey", "Nuevo León"), "guadalupe": ("Guadalupe", "Nuevo León"),
    "san nicolas": ("San Nicolás de los Garza", "Nuevo León"), "apodaca": ("Apodaca", "Nuevo León"),
    "santa catarina": ("Santa Catarina", "Nuevo León"), "san pedro garza garcia": ("San Pedro Garza García", "Nuevo León"),
    "escobedo": ("General Escobedo", "Nuevo León"), "saltillo": ("Saltillo", "Coahuila"),
    "torreon": ("Torreón", "Coahuila"), "monclova": ("Monclova", "Coahuila"),
    "ciudad de mexico": ("Ciudad de México", "CDMX"), "cdmx": ("Ciudad de México", "CDMX"),
    "guadalajara": ("Guadalajara", "Jalisco"), "queretaro": ("Querétaro", "Querétaro"),
    "puebla": ("Puebla", "Puebla"), "leon": ("León", "Guanajuato"), "chihuahua": ("Chihuahua", "Chihuahua"),
    "reynosa": ("Reynosa", "Tamaulipas"), "matamoros": ("Matamoros", "Tamaulipas"),
    "nuevo laredo": ("Nuevo Laredo", "Tamaulipas"), "tampico": ("Tampico", "Tamaulipas"),
    "san luis potosi": ("San Luis Potosí", "San Luis Potosí"), "aguascalientes": ("Aguascalientes", "Aguascalientes"),
    "merida": ("Mérida", "Yucatán"), "cancun": ("Cancún", "Quintana Roo"), "hermosillo": ("Hermosillo", "Sonora"),
    "culiacan": ("Culiacán", "Sinaloa"), "veracruz": ("Veracruz", "Veracruz"), "toluca": ("Toluca", "Estado de México"),
}

SECTOR_KEYWORDS = [
    ("comedor_industrial", r"comedor(es)? industrial(es)?|servicio de alimentos|\bcatering\b|comedores? de (planta|empleados)"),
    ("hotel", r"\bhotel(es|ero|era)?\b"),
    ("restaurante", r"\brestaurant(e|es)?\b|\btaqueria\b|\bcocina\b|\bfranquicia\b|cadena de (restaurantes|comida)"),
    ("industria_alimentaria", r"\bplanta\b|\bfabrica(nte)?\b|\bembutidos\b|\bbotanas\b|panificadora|industria (alimentaria|de alimentos)|procesadora"),
]

URGENCY_HIGH = r"\burgente\b|hoy mismo|a la brevedad|lo antes posible|\basap\b|para manana|\binmediat[oa]\b|sin falta"

_QTY = re.compile(r"(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(toneladas?|tons?\b|t\b|kilogramos?|kilos?|kgs?\b|sacos?|bultos?|cajas?)")
_PHONE = re.compile(r"(?:\+?52[\s-]?)?(?:1[\s-]?)?\(?\d{2,3}\)?[\s.-]?\d{3,4}[\s.-]?\d{4}\b")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_REFS = {
    "quote_folio": re.compile(r"\b(COT-\d{4}-\d{3,})\b", re.I),
    "case_folio": re.compile(r"\b(CASO-\d{4}-\d{3,})\b", re.I),
    "order_ref": re.compile(r"(?:pedido|orden de compra|\boc)\s*(?:no\.?|num\.?|n[uú]mero|#|:)?\s*([A-Z]*-?\d[\w-]{2,})", re.I),
    "lot_ref": re.compile(r"\blote\s*(?:no\.?|num\.?|n[uú]mero|#|:)?\s*([A-Z]*-?\d[\w-]{2,})", re.I),
    "invoice_ref": re.compile(r"\bfactura\s*(?:no\.?|num\.?|#|:)?\s*([A-Z]*-?\d[\w-]{2,})", re.I),
}
_COMPANY_SUFFIX = re.compile(r"([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ&.,\- ]{2,60}?\s(?:S\.?\s?A\.?\s?(?:P\.?I\.?\s)?de\s?C\.?\s?V\.?|S\.?\s?de\s?R\.?\s?L\.?(?:\s?de\s?C\.?\s?V\.?)?))")
_COMPANY_INTRO = re.compile(r"(?:de la empresa|de parte de|trabajo en|somos|represento a|de)\s+((?:Grupo|Restaurante|Restaurantes|Hotel|Comedores|Alimentos|Industrias|Cocina|Taquer[ií]a|Cadena)\s[\wÁÉÍÓÚÑáéíóúñ&.\- ]{2,40}?)(?=[,.\n]| y | en | con |$)")

UNIT_TO_KG = {"t": 1000, "ton": 1000, "tons": 1000, "tonelada": 1000, "toneladas": 1000,
              "kg": 1, "kgs": 1, "kilo": 1, "kilos": 1, "kilogramo": 1, "kilogramos": 1,
              "saco": 25, "sacos": 25, "bulto": 25, "bultos": 25}  # 25 kg = presentación industrial (E11)


@dataclass
class CatalogItem:
    id: str
    sku: str
    name: str
    keywords: list[str]


def _num(s: str) -> float:
    s = s.strip()
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", s):
        return float(re.sub(r"[.,]", "", s))
    return float(s.replace(",", "."))


def extract_quantities(text: str) -> list[dict]:
    out = []
    for m in _QTY.finditer(norm_text(text)):
        unit = m.group(2)
        qty = _num(m.group(1))
        factor = UNIT_TO_KG.get(unit)
        out.append({"qty": qty, "unit": unit, "kg": qty * factor if factor else None,
                    "kg_inferred": unit.startswith(("saco", "bulto"))})
    return out


def extract_phones(text: str) -> list[str]:
    seen, out = set(), []
    for m in _PHONE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        digits = digits[-10:]
        if len(digits) == 10 and digits not in seen:
            seen.add(digits)
            out.append(digits)
    return out


def extract_company(text: str, from_email: str) -> tuple[str | None, str]:
    m = _COMPANY_SUFFIX.search(text)
    if m:
        return m.group(1).strip(" ,."), "razon_social"
    m = _COMPANY_INTRO.search(text)
    if m:
        return m.group(1).strip(" ,."), "texto"
    dom = from_email.split("@")[-1].lower() if "@" in from_email else ""
    if dom and dom not in PUBLIC_DOMAINS:
        base = dom.split(".")[0].replace("-", " ").replace("_", " ")
        return base.title(), "dominio"
    return None, "ninguno"


def extract_products(text: str, catalog: list[CatalogItem]) -> list[dict]:
    t = norm_text(text)
    out = []
    for item in catalog:
        terms = [norm_text(item.name)] + [norm_text(k) for k in item.keywords if k.strip()]
        hit = next((term for term in terms if term and re.search(rf"\b{re.escape(term)}\b", t)), None)
        if hit:
            out.append({"product_id": item.id, "sku": item.sku, "name": item.name, "matched": hit})
    return out


def extract_all(subject: str, body: str, from_email: str, from_name: str | None,
                catalog: list[CatalogItem]) -> dict:
    full = f"{subject}\n{body}"
    t = norm_text(full)
    city = next((v for k, v in CITIES.items() if re.search(rf"\b{k}\b", t)), None)
    sector = next((code for code, rx in SECTOR_KEYWORDS if re.search(rx, t)), None)
    company, company_src = extract_company(full, from_email)
    qtys = extract_quantities(full)
    total_kg = sum(q["kg"] for q in qtys if q["kg"]) or None
    refs = {k: sorted({m.group(1).upper() for m in rx.finditer(full)}) for k, rx in _REFS.items()}
    other_emails = sorted({e.lower() for e in _EMAIL.findall(body)} - {from_email.lower()})
    return {
        "sender_name": from_name,
        "sender_email": from_email.lower(),
        "company": company, "company_source": company_src,
        "phones": extract_phones(full),
        "other_emails": other_emails,
        "city": city[0] if city else None, "state": city[1] if city else None,
        "sector": sector,
        "products": extract_products(full, catalog),
        "quantities": qtys, "total_kg": total_kg,
        "below_minimum": (total_kg is not None and total_kg < 500),
        "urgency": "alta" if re.search(URGENCY_HIGH, t) else "normal",
        "references": {k: v for k, v in refs.items() if v},
    }
