"""Taxonomía de correos (docs/04_CLASIFICADOR.md). Dimensión de INTENCIÓN; la identidad del
remitente (cliente existente / prospecto / proveedor) es una dimensión aparte (D-06)."""

CATEGORIES: dict[str, dict] = {
    "LEAD_NUEVO": {"label": "Nuevo prospecto", "owner": "ventas",
                   "action": "crear_lead", "action_label": "Crear lead y tarea de primer contacto"},
    "SOLICITUD_COTIZACION": {"label": "Solicitud de cotización", "owner": "ventas",
                             "action": "crear_tarea", "action_label": "Crear tarea: preparar cotización"},
    "PEDIDO": {"label": "Pedido / orden de compra", "owner": "administracion",
               "action": "crear_tarea", "action_label": "Crear tarea: capturar pedido en ERP y confirmar"},
    "SEGUIMIENTO_COMERCIAL": {"label": "Seguimiento comercial", "owner": "ventas",
                              "action": "registrar_actividad", "action_label": "Registrar interacción en la oportunidad"},
    "FORMULA_PERSONALIZADA": {"label": "Fórmula / producto especial", "owner": "ventas",
                              "action": "crear_tarea", "action_label": "Crear tarea: levantar brief de fórmula (Ventas + Calidad)"},
    "CALIDAD_RECLAMACION": {"label": "Calidad / reclamación", "owner": "calidad",
                            "action": "abrir_caso", "action_label": "Abrir caso de reclamación (requiere lote)"},
    "DOCUMENTACION_CALIDAD": {"label": "Documentación de calidad", "owner": "calidad",
                              "action": "abrir_caso", "action_label": "Abrir caso de documentación (ficha, certificado)"},
    "LOGISTICA_ENTREGA": {"label": "Logística / entrega", "owner": "atencion",
                          "action": "crear_tarea", "action_label": "Crear tarea: revisar estado de entrega"},
    "PROVEEDOR_COMPRAS": {"label": "Proveedor / compras", "owner": "compras",
                          "action": "reenviar_fuera_crm", "action_label": "Enrutar a Compras (fuera del CRM)"},
    "ADMIN_FACTURACION": {"label": "Administración / facturación", "owner": "administracion",
                          "action": "crear_tarea", "action_label": "Crear tarea para Administración"},
    "SPAM_NO_RELEVANTE": {"label": "Spam / no relevante", "owner": None,
                          "action": "ignorar", "action_label": "Ignorar"},
    "OTRO": {"label": "Otro", "owner": "atencion",
             "action": "revisar", "action_label": "Revisar manualmente"},
}

# Para remitentes desconocidos con intención comercial, la acción cambia a crear lead.
NEW_SENDER_ACTION_OVERRIDE = {
    "SOLICITUD_COTIZACION": ("crear_lead", "Crear lead (con solicitud de cotización) y tarea de primer contacto"),
    "FORMULA_PERSONALIZADA": ("crear_lead", "Crear lead tipo fórmula personalizada"),
    "PEDIDO": ("crear_lead", "Remitente no registrado: crear lead y validar antes de capturar pedido"),
}

ACTIONS = {"crear_lead", "crear_tarea", "abrir_caso", "registrar_actividad", "reenviar_fuera_crm",
           "ignorar", "revisar"}
