"""Reglas ponderadas por categoría. Patrones sobre texto normalizado (minúsculas, sin acentos).

Cada regla: (regex, peso). El asunto cuenta x1.5. Versión: ver engine.CLASSIFIER_VERSION.
"""
import re

R = list[tuple[str, float]]

RULES: dict[str, R] = {
    "SOLICITUD_COTIZACION": [
        (r"\bcotiza(cion|ciones|r|rnos|rme|n)?\b", 3.0), (r"\bprecios?\b", 1.5),
        (r"cuanto (cuesta|cuestan|sale|salen|costaria|nos costaria|me costaria)", 2.5), (r"lista de precios", 2.5),
        (r"(costo|precio) (por|x|del) (kilo|kg|tonelada|bulto|saco)", 2.5), (r"\bpresupuesto\b", 1.5),
        (r"me (pueden|podrian) (pasar|enviar|compartir) (precio|costo)", 2.5),
        (r"(a|en) cuanto (me|nos) (lo |la |los |las )?(dejan|dejarian|dejas|queda)", 3.0), (r"a como (el|me|nos|sale|esta)", 2.5),
        (r"propuesta economica", 3.0), (r"\b(quote|quotation|pricing|price list|how much)\b", 3.0),
    ],
    "LEAD_NUEVO": [
        (r"\bme interesa(n|ria)?\b", 1.5), (r"\b(mas )?informacion\b", 1.2), (r"\bcatalogo\b", 1.5),
        (r"(buscamos|busco|estamos buscando) (un |una )?(nuevo |nuevos )?(proveedor|opciones de proveedor)", 3.0),
        (r"quisiera(mos)? (conocer|saber)", 1.2), (r"(somos|soy) (un|una) (restaurante|hotel|empresa|cadena|comedor|planta|fabrica|panificadora)", 2.0),
        (r"(conocer|conocerlos|trabajar con ustedes|ser (su )?cliente)", 1.2),
        (r"nos (recomendaron|recomendo)|me paso su contacto", 1.5), (r"(vi|vimos|encontre) (su|la) (pagina|anuncio|publicacion)", 1.5),
        (r"(contacto|datos) de (algun|un) (vendedor|asesor|ejecutivo)", 3.0), (r"agendar (una )?(llamada|reunion|cita|visita)", 2.0),
        (r"presentacion de (la|su) empresa|que zonas (cubren|atienden)|nos (pueden|podrian) atender", 2.0),
        (r"evaluando (a )?(nuevos )?proveedores|opciones de proveedores|posibles proveedores", 2.5),
        (r"(potential|new) (supplier|vendor)|looking for a (supplier|vendor)|introduce (myself|our company)", 3.0),
    ],
    "PEDIDO": [
        (r"(adjunto|adjuntamos|envio|enviamos|anexo|comparto|les paso|te paso) (la |el |nuestra |nuestro )?(orden de compra|oc|po|pedido|requisicion)\b", 3.5),
        (r"\b(hacer|levantar|colocar|confirmar|confirmo|confirmamos) (un |el |nuestro |nuestra )?(primer )?(pedido|compra)", 3.0),
        (r"\bfavor de (surtir|programar|enviar(nos)?) \d", 3.0), (r"\bfavor de surtir\b|\bfavor de programar\b", 2.5),
        (r"\bsurt(an|anme|anos|ir)\b", 2.5), (r"\bnecesitamos surtir\b", 2.5), (r"\bpedido (no\.?|num|#)\s*\w+", 1.5),
        (r"\bnuestra orden de compra\b", 3.0), (r"\bquiero pedir\b", 2.5), (r"\breorden\b|\bresurtido\b|\breposicion\b", 2.0),
        (r"(mandan|manden|envien|mandenos) (de nuevo )?lo (mismo|de siempre)", 3.0), (r"confirm(o|amos) la (cotizacion|compra|propuesta)", 3.5),
        (r"pedido de (la|esta) semana|pedido (semanal|de la sucursal)", 2.5), (r"\bpo[ -]?\d", 1.0),
        (r"\b(purchase order|please ship|release(s|ing)? the next shipment|blanket (order|agreement))\b", 3.5),
    ],
    "SEGUIMIENTO_COMERCIAL": [
        (r"\bseguimiento\b", 2.0), (r"(respecto|referente|en relacion|sobre) a? ?(la|lo que nos) (cotizacion|propuesta|propusieron)", 3.0),
        (r"\bcot-\d{4}-\d{3,}|\bcot-\d{3,}", 3.0), (r"(revisamos|analizamos|estamos revisando|ya lo presente|lo platicamos) ", 2.0),
        (r"(mejorar|ajustar|bajar) el precio|\bdescuento\b", 2.0), (r"\bnegociar\b|\bnegociable\b|\bcontraoferta\b", 2.5),
        (r"(retomando|retomo) (la|nuestra) (conversacion|platica)", 2.0), (r"quedo (atento|atenta) a (su|tu) (respuesta|propuesta)", 1.0),
        (r"^(re|rv|fw|fwd): .*(cotizacion|propuesta|cot-)", 3.0),
        (r"(sigo esperando|no me ha llegado|quedaste de (enviar|mandar)|iban a (mandar|enviar)).{0,40}(propuesta|cotizacion)", 3.5),
        (r"(y|que paso con) (lo de )?la (cotizacion|propuesta)", 3.0), (r"gracias por la (propuesta|cotizacion)", 2.5),
        (r"(vigencia|validez) de (la cotizacion|\d+ dias)|dias de credito en lugar", 2.0), (r"propuesta de contrato|acuerdo anual", 2.0),
        (r"(following up|follow up|your proposal|the proposal you sent)", 3.0),
    ],
    "FORMULA_PERSONALIZADA": [
        (r"\bformul(a|acion|aciones|ar)\b", 2.5), (r"(sazonador|condimento|mezcla|premezcla|adobo) (personalizad[oa]|especial|a la medida|exclusiv[oa])", 3.5),
        (r"\ba la medida\b", 2.0), (r"\bmuestras?\b", 1.5), (r"perfil de sabor", 3.0), (r"\breceta\b", 1.5),
        (r"marca propia|\bmaquil(a|en|ar)\b", 2.5), (r"(desarrollar|desarrollen|desarrolle|desarrollo de) (un|una|el|la)? ?(producto|sazonador|mezcla|sabor)", 3.0),
        (r"\b(premezcla|seasoning|blend|prototipos?|panel sensorial)\b", 2.5), (r"(adobo|mezcla|sazonador) (para|tipo) ", 2.0),
        (r"que sepa (tipo|como|a)", 2.5), (r"(private label|custom (blend|seasoning)|co-?packer)", 3.5), (r"estandarizar (el|la) (sabor|adobo|mezcla)", 2.5),
    ],
    "CALIDAD_RECLAMACION": [
        (r"\breclamacion\b|\bqueja\b|\binconformidad\b|\bno conforme\b|no conformidad", 3.5),
        (r"contaminad[oa]s?|materia extrana|cuerpo extrano|\bplaga\b|\binsectos?\b|\bgorgojos?\b|\bpalomilla\b", 4.0),
        (r"\bhumedad\b|\bmoho\b|mal olor|\brancio\b|\bpiedras?\b|\bcabello\b|\bgrumos\b|manchas", 2.5),
        (r"\blote\b", 1.5), (r"\bdevolucion\b|\bdevolver\b|\brecojan\b", 2.0), (r"rechaz(o|amos|ado) (el |del )?(producto|material|lote)", 3.5),
        (r"no cumple (con )?(la )?especificacion|fuera de especificacion", 3.0), (r"producto (danado|defectuoso|en mal estado)", 3.0),
        (r"(sabe|huele|salio|llego) (diferente|raro|a nada|mal|viejo)|(mas|muy) salado|sin sabor|sin olor", 3.0),
        (r"(sacos|costales|bultos|bolsas) (venian |llegaron )?(rotos|mojados|danados|abiertos)|venian rotos", 3.0), (r"\bcuarentena\b|retenid[oa] por", 3.0),
        (r"(non-?conformance|insects?|contaminat|foreign (matter|material)|mold)", 4.0), (r"(causa raiz|acciones correctivas)", 2.5),
    ],
    "DOCUMENTACION_CALIDAD": [
        (r"ficha(s)? tecnica(s)?", 3.5), (r"certificado(s)? de analisis|\bcoa\b", 3.5),
        (r"certificado fssc|certificacion fssc|\bfssc\b|certificado vigente|certificado de inocuidad", 2.5), (r"carta garantia|hoja de seguridad|\balergenos?\b", 3.0),
        (r"(auditoria|cuestionario|evaluacion|alta) (de|como|a) (su planta|proveedor)", 3.0), (r"especificaciones? (tecnicas?|de granulometria)|granulometria", 2.5),
        (r"control de plagas|expediente|proveedor aprobado", 2.0), (r"(technical data sheet|certificate of analysis|spec sheet|allergen)", 3.5),
    ],
    "LOGISTICA_ENTREGA": [
        (r"\bentrega(s|r)?\b", 1.5), (r"no (ha|han) llegado|no llego|todavia no llega|y nada", 3.0), (r"\bguia\b|\brastreo\b|\bpaqueteria\b", 2.5),
        (r"fecha (de|estimada de) entrega|cuando (llega|llegaria|entregan)|a que hora llega", 3.0), (r"\bflete\b|\btransportista\b|\bchofer\b|\bunidad\b", 1.5),
        (r"cita de (descarga|entrega)|horario de recepcion|\banden\b|\bremision\b", 2.5), (r"llego incomplet[oa]|faltante|falto (un|una|\d)", 2.5),
        (r"(direccion|domicilio) de entrega|entregar en (nuestra|la) nueva", 3.0), (r"\bretraso\b|\bretrasad[oa]\b", 2.0),
        (r"(delivery|dock|reschedule|shipment|tracking|truck)", 2.5),
    ],
    "PROVEEDOR_COMPRAS": [
        (r"(le|les|te) (ofrecemos|ofrezco|presentamos)|nuestra empresa (ofrece|exporta|produce)", 3.0),
        (r"\bproforma\b|\bpedimento\b|agente aduanal|despacho aduanal|\bcontenedor(es)?\b|bill of lading|\bb/l\b", 3.5),
        (r"\bfob\b|\bcif\b|\bincoterms?\b|\bexport(adora|amos)\b", 2.5), (r"(su|tu) orden de compra", 3.0),
        (r"\bcosecha\b|disponibilidad de (producto|cosecha)|\bembarque\b|buscamos compradores|tenemos \d+ toneladas", 2.5),
        (r"somos (productores|proveedores|exportadores|distribuidores|fabricantes) de", 3.5),
        (r"(le|te|les) cotizo|(como lo solicitaste|segun lo solicitado).{0,30}cotiz|le envio nuestra lista de precios", 3.5),
        (r"(we are pleased to offer|new crop|dear buyer|kindly revert)", 3.5),
    ],
    "ADMIN_FACTURACION": [
        (r"\bfactura(s|cion|r)?\b|\bcfdi\b|\bxml\b", 3.0), (r"complemento de pago|comprobante de pago|estado de cuenta", 3.5),
        (r"\bpago(s)?\b|\btransferencia\b|\bsaldo\b|\bcobranza\b", 1.5), (r"constancia de situacion fiscal|\brfc\b|uso de cfdi|regimen fiscal", 3.0),
        (r"nota de credito|refactura(r|cion)|\bvencid[oa]s?\b", 3.0), (r"(dias|linea) de credito", 2.0), (r"\bclabe\b|datos bancarios|saldo a favor", 3.0),
        (r"(invoice|payment|remittance)", 2.5),
    ],
    "SPAM_NO_RELEVANTE": [
        (r"unsubscribe|darse de baja|dejar de recibir|para no recibir", 3.0), (r"\bwebinar\b|\bnewsletter\b|\bboletin\b", 2.5),
        (r"\bseo\b|posicionamiento web|marketing digital para su|clientes nuevos al mes|base de datos (actualizada )?de \d", 3.0),
        (r"gana dinero|haz clic|haga clic|oferta limitada|\bcripto|click here", 3.5),
        (r"\bprestamo(s)?\b|credito inmediato", 2.5), (r"(felicidades|has sido seleccionad[oa]|resulto ganador)", 3.0),
        (r"(verifique|valide|actualice) (sus datos|su cuenta|su informacion)|sera suspendid|ha sido suspendid|actividad inusual|detectamos irregularidades", 4.5),
        (r"su paquete (esta |no pudo ser |fue )?(retenido|entregado por falta)|(mailbox|storage) (limit|full)|validate your", 4.5),
        (r"\bpromocion\b|\% de descuento|reserve su stand|agende una demo|demo gratis", 2.5),
    ],
    "OTRO": [
        (r"curriculum|\bcv\b|solicitud de empleo|\bvacante\b|me gustaria (trabajar|formar parte)|bolsa de trabajo", 4.0),
        (r"\bdonativo\b|\bdonacion\b|\bkermes\b|banco de alimentos|patrocinio", 4.0),
        (r"visita (academica|escolar|a su planta para un proyecto)|\bestudiantes\b|practicas profesionales|servicio social|\bdocente\b", 3.5),
        (r"felices fiestas|feliz navidad|muchas gracias por todo", 2.5),
        (r"respuesta automatica|automatic reply|auto-?reply|out of (the )?office|fuera de la oficina", 5.0),
    ],
}

# Prioridad para correos mixtos (data/eval/GUIA_ETIQUETADO.md): si la categoría de mayor consecuencia
# tiene evidencia fuerte, absorbe el puntaje de las de menor prioridad presentes.
PRIORITY_ABSORB = [
    ("CALIDAD_RECLAMACION", 3.0, ["LOGISTICA_ENTREGA", "ADMIN_FACTURACION", "PEDIDO", "FORMULA_PERSONALIZADA"]),
    ("PEDIDO", 3.0, ["LOGISTICA_ENTREGA", "ADMIN_FACTURACION", "SOLICITUD_COTIZACION"]),
    ("SEGUIMIENTO_COMERCIAL", 3.0, ["SOLICITUD_COTIZACION"]),
    ("LOGISTICA_ENTREGA", 3.0, ["ADMIN_FACTURACION"]),
    ("SPAM_NO_RELEVANTE", 4.0, ["ADMIN_FACTURACION", "LOGISTICA_ENTREGA", "SOLICITUD_COTIZACION", "LEAD_NUEVO"]),
    ("OTRO", 3.5, ["LEAD_NUEVO", "FORMULA_PERSONALIZADA", "PEDIDO", "SEGUIMIENTO_COMERCIAL"]),
]

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
