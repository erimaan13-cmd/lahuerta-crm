"""Reglas del pipeline comercial (docs/02_PLAN.md §4, DECISION_LOG D-07/D-08)."""

STAGE_LABELS = {
    "requerimiento": "Requerimiento",
    "desarrollo_formula": "Desarrollo de fórmula",
    "muestra_enviada": "Muestra enviada",
    "muestra_aprobada": "Muestra aprobada",
    "cotizacion": "Cotización",
    "negociacion": "Negociación",
    "ganada": "Ganada",
    "perdida": "Perdida",
}
OPEN_STAGES = ["requerimiento", "desarrollo_formula", "muestra_enviada", "muestra_aprobada",
               "cotizacion", "negociacion"]
CLOSED_STAGES = {"ganada", "perdida"}

TRANSITIONS: dict[str, dict[str, set[str]]] = {
    "estandar": {
        "requerimiento": {"cotizacion", "perdida"},
        "cotizacion": {"negociacion", "ganada", "perdida"},
        "negociacion": {"cotizacion", "ganada", "perdida"},
    },
    "formula_personalizada": {
        "requerimiento": {"desarrollo_formula", "perdida"},
        "desarrollo_formula": {"muestra_enviada", "perdida"},
        "muestra_enviada": {"muestra_aprobada", "desarrollo_formula", "perdida"},
        "muestra_aprobada": {"cotizacion", "perdida"},
        "cotizacion": {"negociacion", "ganada", "perdida"},
        "negociacion": {"cotizacion", "ganada", "perdida"},
    },
    "recompra": {
        "requerimiento": {"cotizacion", "perdida"},
        "cotizacion": {"negociacion", "ganada", "perdida"},
        "negociacion": {"cotizacion", "ganada", "perdida"},
    },
}
OPP_TYPES = set(TRANSITIONS)

STAGE_OWNER_ROLE = {
    "requerimiento": "ventas", "desarrollo_formula": "calidad", "muestra_enviada": "ventas",
    "muestra_aprobada": "ventas", "cotizacion": "ventas", "negociacion": "ventas",
    "ganada": "administracion", "perdida": "ventas",
}


def stages_for(opp_type: str) -> list[str]:
    if opp_type == "formula_personalizada":
        return OPEN_STAGES + ["ganada", "perdida"]
    return ["requerimiento", "cotizacion", "negociacion", "ganada", "perdida"]


def allowed_next(opp_type: str, stage: str) -> set[str]:
    return TRANSITIONS.get(opp_type, {}).get(stage, set())
