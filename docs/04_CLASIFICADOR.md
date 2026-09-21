# 04 · Clasificador automático de correos

## Arquitectura (desacoplada)

`EMAIL PROVIDER → INGESTA → NORMALIZACIÓN → CLASIFICACIÓN → EXTRACCIÓN → VINCULACIÓN CRM → ENRUTAMIENTO → REVISIÓN HUMANA`

| Etapa | Módulo | Qué hace |
|---|---|---|
| Proveedor | `app/integrations/email_providers.py` | `EmlDirectoryProvider` (archivos .eml reales), `MockMailboxProvider` (JSON sintético), `GmailProvider` (P1, lanza `NotImplementedError`). Todos solo lectura. |
| Ingesta | `services/email_pipeline.ingest/process_raw` | Idempotente por `(provider, Message-ID)`; correos sin remitente válido se cuentan como error sin detener el lote |
| Normalización | `classifier/normalize.py` | HTML→texto, elimina historial citado ("El … escribió:", ">"), texto sin acentos para reglas |
| Identidad del remitente | `email_pipeline.resolve_sender` | contacto · lead · dominio de cuenta · proveedor · desconocido (dimensión ortogonal a la categoría, D-06) |
| Clasificación | `classifier/rules.py` + `engine.py` | Reglas ponderadas (asunto ×1.5) + ajustes por contexto; `confidence = top / (Σ + 1)`; `margin = (top − 2º) / (Σ + 1)` |
| Extracción | `classifier/extract.py` | remitente, correo, empresa (razón social / texto / dominio / CRM), teléfonos (10 dígitos MX), ciudad/estado, sector, productos (catálogo inyectado), cantidades→kg (t, kg, saco/bulto=25 kg*), urgencia, folios COT/CASO, pedido/OC, lote, factura |
| Vinculación | `email_pipeline.link_references` | contacto→cuenta; COT→cotización→oportunidad; CASO/lote→caso; pedido→OrderReference. Crea actividad "correo" en la entidad (reversible) |
| Enrutamiento | `classifier/taxonomy.py` | `suggested_owner` y `suggested_action` por categoría; remitente nuevo con intención comercial → `crear_lead` |
| Revisión | `email_pipeline.review / apply_suggestion` | Confirmar/corregir (etiqueta auditada) y aplicar la acción **solo con clic humano** |

## Taxonomía (ajustada tras la investigación)

| Código | Etiqueta | Dueño sugerido | Acción sugerida | Cambio vs hipótesis |
|---|---|---|---|---|
| LEAD_NUEVO | Nuevo prospecto | ventas | crear_lead | Solo interés general; con cotización/fórmula/pedido su puntaje **refuerza** esa intención |
| SOLICITUD_COTIZACION | Solicitud de cotización | ventas | crear_tarea (remitente nuevo: crear_lead) | — |
| PEDIDO | Pedido / orden de compra | administracion | crear_tarea | — |
| SEGUIMIENTO_COMERCIAL | Seguimiento comercial | ventas | registrar_actividad | — |
| FORMULA_PERSONALIZADA | Fórmula / producto especial | ventas (+calidad) | crear_tarea (nuevo: crear_lead) | Evidencia E06 |
| CALIDAD_RECLAMACION | Calidad / reclamación | calidad | abrir_caso | **Siempre a revisión** |
| DOCUMENTACION_CALIDAD | Documentación de calidad | calidad | abrir_caso (documentación) | **Nueva** (E03, E25) |
| LOGISTICA_ENTREGA | Logística / entrega | atencion | crear_tarea | — |
| PROVEEDOR_COMPRAS | Proveedor / compras | compras (fuera del CRM) | reenviar_fuera_crm | Proveedores no son entidades del CRM |
| ADMIN_FACTURACION | Administración / facturación | administracion | crear_tarea | — |
| SPAM_NO_RELEVANTE | Spam / no relevante | — | ignorar | — |
| OTRO | Otro | atencion | revisar | **Siempre a revisión** |
| ~~Cliente existente~~ | — | — | — | **Eliminada como categoría**: pasa a ser la dimensión `sender_kind` / `crm_link` (D-06) |

## Método, umbral y revisión humana

- Método: **reglas deterministas** (explicables: la UI muestra qué patrón disparó). Puerto `LLMClient` listo para modo híbrido: solo se consulta si hay duda **y** `CRM_LLM_ENABLED=true`; si LLM y reglas discrepan, va a revisión.
- **Needs Review** si: `confidence < 0.60` **o** `margin < 0.15` **o** categoría sensible (`CALIDAD_RECLAMACION`, `OTRO`). Configurables por variables de entorno.
- Estados: `auto` → `confirmado`/`corregido` → `aplicado`; `needs_review` exige confirmar/corregir antes de aplicar.
- Nunca: enviar respuestas, borrar, archivar, mover ni etiquetar en el buzón.

## Resultado sobre el corpus sintético (18 correos)

`python -m scripts.eval_classifier`: exactitud 16/18 (89 %); 14 auto-clasificados, **14/14 correctos**; los 2 errores (correo mixto y correo en inglés) cayeron en Needs Review. **Advertencia:** es el mismo corpus usado para ajustar reglas → cifra optimista; no representa correos reales.

\* La conversión saco/bulto = 25 kg se basa en la presentación industrial publicada (E11) y se marca como inferida.
