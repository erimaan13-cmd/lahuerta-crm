# Guía de etiquetado del corpus de evaluación

Una sola etiqueta por correo: **la intención que define quién debe actuar primero**.

| Situación | Etiqueta |
|---|---|
| Remitente sin relación previa que pide precio o cotización | SOLICITUD_COTIZACION |
| Remitente sin relación previa que pide información, catálogo o contacto, sin pedir precio | LEAD_NUEVO |
| Cliente que pide precio de algo nuevo | SOLICITUD_COTIZACION |
| Pedido firme (orden de compra, "surtan", "confirmo", cantidades para entregar) | PEDIDO |
| Respuesta a una cotización o propuesta, negociación, "¿qué pasó con…?" comercial | SEGUIMIENTO_COMERCIAL |
| Mezcla, sazonador o producto a la medida; muestras de desarrollo; maquila | FORMULA_PERSONALIZADA |
| Problema de calidad o inocuidad del producto recibido (aunque mencione también entrega o factura) | CALIDAD_RECLAMACION |
| Solicitud de fichas técnicas, certificados, COA, cartas garantía, cuestionarios o alta de proveedor | DOCUMENTACION_CALIDAD |
| Estado, fecha, retraso o faltante de una entrega **sin daño al producto** | LOGISTICA_ENTREGA |
| Proveedor o importación que vende, cotiza o envía documentos a La Huerta | PROVEEDOR_COMPRAS |
| Facturas, CFDI, pagos, crédito, datos fiscales | ADMIN_FACTURACION |
| Publicidad no solicitada, phishing, boletines | SPAM_NO_RELEVANTE |
| Sin intención identificable o fuera de alcance (vacantes, saludos, llamadas sin contexto) | OTRO |

Reglas de desempate para correos mixtos (de mayor a menor prioridad):
CALIDAD_RECLAMACION > PEDIDO > LOGISTICA_ENTREGA > ADMIN_FACTURACION > SEGUIMIENTO_COMERCIAL > SOLICITUD_COTIZACION.

Procedimiento anti-sesgo:
1. `test_holdout.json` se escribió **antes** de modificar las reglas y se congeló con SHA-256 (`HOLDOUT.sha256`).
2. Las reglas solo se ajustan mirando `dev.json`.
3. El held-out se evalúa una sola vez al final; si se ajusta algo después de verlo, ese resultado deja de ser held-out y se reporta como tal.
