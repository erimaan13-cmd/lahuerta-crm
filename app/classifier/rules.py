"""Reglas ponderadas por categoría. Patrones sobre texto normalizado (minúsculas, sin acentos).

Cada regla: (regex, peso). El asunto cuenta x1.5. Versión: ver engine.CLASSIFIER_VERSION.
"""
import re

R = list[tuple[str, float]]

RULES: dict[str, R] = {
    "SOLICITUD_COTIZACION": [
        (r"\bcotiza(cion|ciones|r|rnos|rme|n)?\b", 3.0), (r"\bprecios?\b", 1.5),
        (r"cuanto (cuesta|cuestan|sale)", 2.5), (r"lista de precios", 2.5),
        (r"(costo|precio) (por|x) (kilo|kg)", 2.5), (r"\bpresupuesto\b", 1.5),
        (r"me (pueden|podrian) (pasar|enviar|compartir) (precio|costo)", 2.5),
    ],
    "LEAD_NUEVO": [
        (r"\bme interesa(n|ria)?\b", 1.5), (r"\b(mas )?informacion\b", 1.2), (r"\bcatalogo\b", 1.5),
        (r"(buscamos|busco|estamos buscando) (un )?(nuevo )?proveedor", 3.0),
        (r"quisiera(mos)? (conocer|saber)", 1.2), (r"(somos|soy) (un|una) (restaurante|hotel|empresa|cadena|comedor|planta|fabrica)", 2.0),
        (r"(conocer|conocerlos|trabajar con ustedes|ser (su )?cliente)", 1.2),
        (r"nos (recomendaron|recomendo)", 1.5), (r"(vi|vimos|encontre) (su|la) (pagina|anuncio|publicacion)", 1.5),
    ],
    "PEDIDO": [
        (r"(adjunto|adjuntamos|envio|enviamos|anexo) (la |nuestra )?(orden de compra|oc)\b", 3.5),
        (r"\b(hacer|levantar|colocar|confirmar|confirmo|confirmamos) (un |el |nuestro )?pedido", 3.0),
        (r"\bfavor de surtir\b", 3.0), (r"\bnecesitamos surtir\b", 2.5), (r"\bpedido (no\.?|num|#)\s*\w+", 1.5),
        (r"\bnuestra orden de compra\b", 3.0), (r"\bquiero pedir\b", 2.5), (r"\breorden\b|\bresurtido\b", 2.0),
    ],
    "SEGUIMIENTO_COMERCIAL": [
        (r"\bseguimiento\b", 2.0), (r"(respecto|referente|en relacion) a la (cotizacion|propuesta)", 3.0),
        (r"\bcot-\d{4}-\d{3,}", 3.0), (r"(revisamos|analizamos|estamos revisando) (la|su) (cotizacion|propuesta)", 3.0),
        (r"(mejorar|ajustar) el precio|\bdescuento\b", 2.0), (r"\bnegociar\b|\bcontraoferta\b", 2.0),
        (r"(retomando|retomo) (la|nuestra) (conversacion|platica)", 2.0), (r"quedo (atento|atenta) a (su|tu) (respuesta|propuesta)", 1.0),
    ],
    "FORMULA_PERSONALIZADA": [
        (r"\bformul(a|acion|aciones|ar)\b", 2.5), (r"(sazonador|condimento|mezcla) (personalizad[oa]|especial|a la medida|exclusiv[oa])", 3.5),
        (r"\ba la medida\b", 2.0), (r"\bmuestra(s)?\b", 1.5), (r"perfil de sabor", 3.0), (r"\breceta\b", 1.5),
        (r"marca propia|\bmaquila\b", 2.5), (r"(desarrollar|desarrollen|desarrollo de) (un|una|el|la)? ?(producto|sazonador|mezcla)", 3.0),
    ],
    "CALIDAD_RECLAMACION": [
        (r"\breclamacion\b|\bqueja\b|\binconformidad\b|\bno conforme\b", 3.5),
        (r"contaminad[oa]s?|materia extrana|cuerpo extrano|\bplaga\b|\binsectos?\b|\bgorgojos?\b", 4.0),
        (r"\bhumedad\b|\bmoho\b|mal olor|\brancio\b|\bpiedras?\b|\bcabello\b", 2.5),
        (r"\blote\b", 1.5), (r"\bdevolucion\b|\bdevolver\b", 2.0), (r"rechaz(o|amos|ado) (el |del )?(producto|material|lote)", 3.5),
        (r"no cumple (con )?(la )?especificacion", 3.0), (r"producto (danado|defectuoso|en mal estado)", 3.0),
    ],
    "DOCUMENTACION_CALIDAD": [
        (r"ficha(s)? tecnica(s)?", 3.5), (r"certificado(s)? de analisis|\bcoa\b", 3.5),
        (r"certificado fssc|certificacion fssc|\bfssc\b", 2.0), (r"carta garantia|hoja de seguridad|\balergenos?\b", 3.0),
        (r"(auditoria|cuestionario|evaluacion|alta) (de|como) proveedor", 3.0), (r"especificaciones tecnicas", 2.5),
    ],
    "LOGISTICA_ENTREGA": [
        (r"\bentrega(s|r)?\b", 1.5), (r"no (ha|han) llegado|no llego", 3.0), (r"\bguia\b|\brastreo\b|\bpaqueteria\b", 2.5),
        (r"fecha (de|estimada de) entrega|cuando (llega|llegaria|entregan)", 3.0), (r"\bflete\b|\btransportista\b", 1.5),
        (r"cita de (descarga|entrega)|horario de recepcion|\banden\b", 3.0), (r"llego incomplet[oa]|faltante", 2.5),
    ],
    "PROVEEDOR_COMPRAS": [
        (r"(le|les) (ofrecemos|ofrecemos nuestra|presentamos)|nuestra empresa (ofrece|exporta|produce)", 3.0),
        (r"\bproforma\b|\bpedimento\b|agente aduanal|\bcontenedor(es)?\b|bill of lading|\bb/l\b", 3.5),
        (r"\bfob\b|\bcif\b|\bincoterms?\b|\bexport(adora|amos)\b", 2.5), (r"(su|tu) orden de compra", 3.0),
        (r"\bcosecha\b|disponibilidad de (producto|cosecha) de nuestra parte|\bembarque\b", 2.0),
        (r"somos (productores|proveedores|exportadores|distribuidores) de", 3.0),
    ],
    "ADMIN_FACTURACION": [
        (r"\bfactura(s|cion|r)?\b|\bcfdi\b|\bxml\b", 3.0), (r"complemento de pago|comprobante de pago|estado de cuenta", 3.5),
        (r"\bpago(s)?\b|\btransferencia\b|\bsaldo\b|\bcobranza\b", 1.5), (r"constancia de situacion fiscal|\brfc\b|uso de cfdi", 3.0),
        (r"nota de credito|refactura(r|cion)|\bvencid[oa]s?\b", 3.0), (r"(dias|linea) de credito", 2.0),
    ],
    "SPAM_NO_RELEVANTE": [
        (r"unsubscribe|darse de baja|dejar de recibir", 3.0), (r"\bwebinar\b|\bnewsletter\b", 2.5),
        (r"\bseo\b|posicionamiento web|marketing digital para su", 3.0), (r"gana dinero|haz clic|oferta limitada|\bcripto", 3.5),
        (r"\bprestamo(s)?\b|credito inmediato", 2.5), (r"(felicidades|has sido seleccionad[oa])", 3.0),
    ],
}

_COMPILED = {cat: [(re.compile(p), w) for p, w in rules] for cat, rules in RULES.items()}
SUBJECT_WEIGHT = 1.5


def score(subject_norm: str, body_norm: str) -> tuple[dict[str, float], dict[str, list[str]]]:
    """Devuelve puntajes por categoría y las evidencias (patrones que dispararon)."""
    scores: dict[str, float] = {}
    hits: dict[str, list[str]] = {}
    for cat, rules in _COMPILED.items():
        s = 0.0
        for rx, w in rules:
            m_sub, m_body = rx.search(subject_norm), rx.search(body_norm)
            if m_sub:
                s += w * SUBJECT_WEIGHT
                hits.setdefault(cat, []).append(f"asunto:'{m_sub.group(0)}'")
            elif m_body:
                s += w
                hits.setdefault(cat, []).append(f"cuerpo:'{m_body.group(0)}'")
        if s:
            scores[cat] = round(s, 3)
    return scores, hits
