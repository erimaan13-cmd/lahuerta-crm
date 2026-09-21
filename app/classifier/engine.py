"""Motor del clasificador (componente desacoplado: no importa modelos ni sesiones de BD).

Entrada: ClassifierInput (texto + contexto del remitente + catálogo).
Salida: ClassifierResult con classification, confidence, extracted_entities, suggested_owner,
suggested_action y la decisión de revisión humana. La vinculación CRM la hace el servicio.
"""
from dataclasses import dataclass, field

from app import config
from app.classifier import normalize, rules, taxonomy
from app.classifier.extract import CatalogItem, extract_all
from app.classifier.llm import LLMClient, NullLLMClient

CLASSIFIER_VERSION = "rules-1.1"
PRIOR_MASS = 1.0  # masa de "incertidumbre": poca evidencia ⇒ baja confianza


@dataclass
class ClassifierInput:
    subject: str
    body: str
    from_email: str
    from_name: str | None = None
    sender_kind: str = "desconocido"  # contacto | lead | cuenta_dominio | proveedor | desconocido
    catalog: list[CatalogItem] = field(default_factory=list)


@dataclass
class ClassifierResult:
    classification: str
    confidence: float
    margin: float
    scores: dict
    evidence: dict
    extracted_entities: dict
    suggested_owner: str | None
    suggested_action: str
    suggested_action_label: str
    needs_review: bool
    review_reason: str | None
    method: str
    version: str = CLASSIFIER_VERSION


def _apply_context(scores: dict[str, float], sender_kind: str, ents: dict) -> dict[str, float]:
    s = dict(scores)
    if sender_kind == "proveedor":
        # un proveedor conocido casi siempre escribe como proveedor (incluso si habla de facturas o precios)
        others = max([v for k, v in s.items() if k != "PROVEEDOR_COMPRAS"] or [0])
        s["PROVEEDOR_COMPRAS"] = max(s.get("PROVEEDOR_COMPRAS", 0), others) + 3.0
    if sender_kind in ("contacto", "lead", "cuenta_dominio"):
        s.pop("LEAD_NUEVO", None)  # ya existe en el CRM: no es prospecto nuevo
        s.pop("SPAM_NO_RELEVANTE", None)
    elif sender_kind == "desconocido":
        if (ents.get("products") or ents.get("total_kg")) and not any(
                k in s for k in ("CALIDAD_RECLAMACION", "PROVEEDOR_COMPRAS", "ADMIN_FACTURACION")):
            s["LEAD_NUEVO"] = s.get("LEAD_NUEVO", 0) + 1.0  # intención comercial de remitente nuevo
        # "Prospecto nuevo" es compatible con una intención comercial específica: no compite, la refuerza.
        specific = [k for k in ("SOLICITUD_COTIZACION", "FORMULA_PERSONALIZADA", "PEDIDO") if k in s]
        if specific and "LEAD_NUEVO" in s:
            best = max(specific, key=lambda k: s[k])
            s[best] += s.pop("LEAD_NUEVO")
    if ents["references"].get("quote_folio"):
        s["SEGUIMIENTO_COMERCIAL"] = s.get("SEGUIMIENTO_COMERCIAL", 0) + 1.0
    if ents["references"].get("lot_ref") and "CALIDAD_RECLAMACION" in s:
        s["CALIDAD_RECLAMACION"] += 1.0
    for winner, min_score, losers in rules.PRIORITY_ABSORB:
        if s.get(winner, 0) >= min_score:
            for loser in losers:
                if loser in s:
                    s[winner] += s.pop(loser)
    return s


def decide(scores: dict[str, float]) -> tuple[str, float, float]:
    if not scores:
        return "OTRO", 0.0, 0.0
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    total = sum(scores.values()) + PRIOR_MASS
    top_cat, top = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    return top_cat, round(top / total, 3), round((top - second) / total, 3)


def classify(inp: ClassifierInput, llm: LLMClient | None = None) -> ClassifierResult:
    llm = llm or NullLLMClient()
    body_clean = normalize.clean_body(inp.body)
    subj_n, body_n = normalize.norm_text(inp.subject), normalize.norm_text(body_clean)
    ents = extract_all(inp.subject, body_clean, inp.from_email, inp.from_name, inp.catalog)
    raw_scores, evidence = rules.score(subj_n, body_n)
    scores = _apply_context(raw_scores, inp.sender_kind, ents)
    category, conf, margin = decide(scores)
    method = "rules"

    reasons = []
    if conf < config.CLASSIFIER_THRESHOLD:
        reasons.append(f"confianza {conf:.2f} < {config.CLASSIFIER_THRESHOLD:.2f}")
    if margin < config.CLASSIFIER_MIN_MARGIN:
        reasons.append(f"margen {margin:.2f} < {config.CLASSIFIER_MIN_MARGIN:.2f}")

    # Paso híbrido: solo si hay duda y el LLM está habilitado
    if reasons and config.LLM_ENABLED:
        ans = llm.classify(inp.subject, body_clean, list(taxonomy.CATEGORIES))
        if ans and ans[0] in taxonomy.CATEGORIES:
            method = "hybrid"
            if ans[0] == category:  # coinciden reglas y LLM ⇒ se acepta con la confianza mayor
                conf = max(conf, ans[1])
                reasons = [] if conf >= config.CLASSIFIER_THRESHOLD else reasons
            else:
                reasons.append(f"reglas={category} vs llm={ans[0]}")

    if category in config.CLASSIFIER_ALWAYS_REVIEW:
        reasons.append(f"categoría sensible ({category}) siempre requiere revisión")

    meta = taxonomy.CATEGORIES[category]
    action, label = meta["action"], meta["action_label"]
    if inp.sender_kind == "desconocido" and category in taxonomy.NEW_SENDER_ACTION_OVERRIDE:
        action, label = taxonomy.NEW_SENDER_ACTION_OVERRIDE[category]

    return ClassifierResult(classification=category, confidence=conf, margin=margin, scores=scores,
                            evidence=evidence, extracted_entities=ents, suggested_owner=meta["owner"],
                            suggested_action=action, suggested_action_label=label,
                            needs_review=bool(reasons), review_reason="; ".join(reasons) or None,
                            method=method)
