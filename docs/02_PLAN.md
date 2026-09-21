# 02 · Plan — Requerimientos, dominio, pipeline y arquitectura

> Fase PLANIFICAR. Cada requerimiento cita la evidencia (`E##`, ver `01_INVESTIGACION.md`) que lo origina. Los IDs `RF-##`/`RNF-##` se usan en la `TRACEABILITY_MATRIX`.

## 1. Requerimientos funcionales

### P0 — indispensables para el MVP (demo)

| ID | Requerimiento | Evidencia | Criterio de aceptación |
|---|---|---|---|
| RF-01 | Capturar leads con los campos de los formularios públicos y su **origen** (`web_contacto`, `web_catalogo`, `whatsapp`, `telefono`, `email`, `google_ads`, `meta_ads`, `linkedin`, `referido`, `otro`) | E13–E15, E20 | Lead creado vía UI y API; nombre + (email o teléfono) obligatorios |
| RF-02 | Deduplicación básica al crear lead | E17, E19 | Mismo email → no crea duplicado (registra actividad en el existente); mismo teléfono normalizado o mismo dominio corporativo → marca `possible_duplicate_of` |
| RF-03 | Calificar lead (volumen, sector, ciudad); marcar **bajo mínimo** (< 500 kg) | E02, E15 | Estados `nuevo → contactado → calificado / descartado`; bandera `below_minimum` calculada |
| RF-04 | Convertir lead → Cuenta + Contacto (+ Oportunidad) reutilizando cuenta existente por dominio | E01 | Lead queda `convertido`, con vínculos; no se duplica cuenta con mismo dominio |
| RF-05 | Oportunidades con tipo `estandar` / `formula_personalizada` / `recompra`, producto(s) y volumen kg | E06, E11 | Oportunidad creada ligada a cuenta |
| RF-06 | Pipeline con transiciones **validadas** por etapa y subflujo de fórmula; motivo de pérdida obligatorio | E06, E14 | Transición inválida → error 422 explicativo |
| RF-07 | Registrar interacciones (llamada, correo, WhatsApp, reunión, nota) | E13 | Actividad visible en la cuenta/lead/oportunidad |
| RF-08 | Tareas con responsable y vencimiento; **tarea automática de primer contacto** al crear lead | E14 ("enseguida") | Tarea creada con vencimiento +4 h |
| RF-09 | Búsqueda global y filtros | — | Busca por nombre, empresa, email, teléfono; filtros por estado/sector/origen/etapa |
| RF-10 | Ingesta de correo mediante **adaptador** (archivos `.eml` y buzón simulado), idempotente por `Message-ID` | E17 | Reingesta no duplica |
| RF-11 | Normalización (HTML→texto, respuesta citada, firma, acentos) | — | Texto limpio guardado |
| RF-12 | Clasificación con categoría y **confianza** | E17 | Cada correo tiene `classification`, `confidence` |
| RF-13 | Extracción de entidades (remitente, empresa, teléfono, ciudad, sector, producto, cantidad, unidad, urgencia, referencias) | E09–E11 | `extracted_entities` JSON |
| RF-14 | Vinculación al CRM (contacto, cuenta, lead, oportunidad, caso, pedido) | — | `crm_entity_link` cuando hay coincidencia |
| RF-15 | Sugerir responsable y acción; aplicar sugerencia **solo por acción humana** | — | Sin creación automática de entidades |
| RF-16 | Bandeja **Needs Review** cuando confianza < umbral, margen bajo o categoría sensible | — | Confirmar/corregir; la corrección queda auditada como etiqueta |
| RF-17 | Dashboard mínimo | — | Leads, oportunidades, pipeline, tareas pendientes, correos por categoría, Needs Review, clientes, cotizaciones |
| RF-18 | Casos (reclamación / documentación / entrega / facturación) con severidad y `lot_reference` | E03, E24 | Caso de calidad no se cierra sin lote |
| RF-19 | Cotización básica (partidas: producto, kg, empaque, precio/kg) ligada a oportunidad | E10, E14 | Mover a etapa `cotizacion` requiere al menos una cotización |
| RF-20 | Autenticación y RBAC por rol | — | Rol sin permiso → 403 |
| RF-21 | Bitácora de auditoría de toda mutación | — | `AuditEvent` con actor, acción, antes/después |
| RF-22 | Referencias de pedido (`OrderReference`) mediante adaptador ERP **simulado** | E05 | Estado y fecha prometida visibles en la cuenta |
| RF-23 | Datos de demostración sintéticos claramente marcados | — | Prefijo/etiqueta `[DEMO]` |

### P1 — inmediatamente después

RF-30 Adaptador Gmail/Workspace real (solo lectura, OAuth) · RF-31 Clasificador LLM activado en modo híbrido con presupuesto · RF-32 Webhook del formulario web con anti-spam · RF-33 WhatsApp Business (lectura) · RF-34 SLA en horas hábiles L–V 8–17 (E13) · RF-35 Fusión manual de duplicados · RF-36 PDF de cotización y versionado · RF-37 Aprobación de precio especial · RF-38 Alerta de recompra (cliente sin pedido en N días) · RF-39 Integración ERP real (clientes, pedidos, crédito) · RF-40 Métricas del clasificador (precisión por categoría desde las correcciones) · RF-41 Exportar/anonimizar contacto (ARCO, E16) · RF-42 Notificaciones internas · RF-43 Despliegue en PostgreSQL gestionado.

### P2 — escalamiento (congelado durante el MVP)

Disponibilidad de inventario desde WMS · apertura de no conformidades en QMS · portal de clientes · pronóstico de ventas · automatización de marketing · canal retail (visión, E12) · modelo ML entrenado con las etiquetas acumuladas · respuestas asistidas (borradores) con aprobación humana.

## 2. Requerimientos no funcionales

| ID | Tema | Requisito MVP | Evolución |
|---|---|---|---|
| RNF-01 | Seguridad | Contraseñas con PBKDF2-SHA256 + sal; cookie de sesión firmada `HttpOnly`, `SameSite=Lax`; secretos solo por variables de entorno | HTTPS, CSRF tokens, rotación de secretos |
| RNF-02 | Autenticación | Usuario/contraseña local | SSO Google Workspace (OIDC) |
| RNF-03 | Autorización / RBAC | Matriz rol→permiso en código, verificada en cada endpoint | Permisos por registro (propietario/equipo) |
| RNF-04 | Privacidad | Solo datos sintéticos; no se guardan datos financieros/fiscales (E16) | Consentimiento y ARCO |
| RNF-05 | Auditoría | `AuditEvent` inmutable (sin endpoint de edición/borrado) | Exportación a almacenamiento WORM |
| RNF-06 | Trazabilidad | `EVIDENCE → RF → entidad → módulo → prueba` | Mantener matriz al día |
| RNF-07 | Mantenibilidad | Capas: rutas → servicios → modelos; clasificador y adaptadores aislados | Paquetes separados |
| RNF-08 | Escalabilidad | SQLAlchemy, SQL portable; IDs UUID-texto; sin funciones exclusivas de SQLite | PostgreSQL, colas, workers |
| RNF-09 | Observabilidad | Logging estructurado (JSON) + `/health` + `X-Request-ID` | Métricas y trazas (OpenTelemetry) |
| RNF-10 | Respaldos | Base SQLite en un archivo; script de respaldo con marca de tiempo | Backups gestionados PITR |
| RNF-11 | Portabilidad de datos | Exportación JSON de entidades (`/api/export`) | CSV, API pública |
| RNF-12 | Integraciones | Interfaces `EmailProvider`, `ErpAdapter`, `LLMClient`; outbox `IntegrationEvent` | Adaptadores reales |
| RNF-13 | Costo | $0 de infraestructura para el MVP | Postgres gestionado de nivel gratuito/bajo |
| RNF-14 | Rendimiento | < 300 ms por página con ~10 k registros (índices en email, dominio, estado) | Paginación, caché |

## 3. Modelo de dominio

Convenciones: `id` = UUID en texto; `created_at/updated_at` UTC; `owner_id` → `User`. Nombres en inglés en código; etiquetas en español en la UI.

| Entidad | Atributos clave | Relaciones (cardinalidad) | Estados / lifecycle | Restricciones |
|---|---|---|---|---|
| **User** | email, full_name, role, team, password_hash, is_active | 1:N Task, Opportunity (owner) | activo/inactivo | email único |
| **Role** (enum en código) | `admin`, `ventas`, `atencion`, `calidad`, `administracion`, `lectura` | — | — | — |
| **Sector** (catálogo) | code, name | 1:N Account, Lead | — | configurable (E22) |
| **Product** (catálogo) | sku, name, category (`especia`, `grano`, `semilla`, `chile_seco`, `condimento`), is_custom, keywords | N:M Opportunity vía ProductInterest | activo | lista sintética (E22) |
| **Lead** | full_name, company_name, email, phone, city, state, sector_code, product_interest_text, volume_band (`500kg_1t`, `mas_1t`, `menor_500kg`, `desconocido`), est_volume_kg, message, source, campaign, status, below_minimum, possible_duplicate_of_id, converted_account_id/contact_id/opportunity_id, consent_source | N:1 User (owner); 0..1 Account/Contact tras conversión | `nuevo → contactado → calificado → convertido`; `→ descartado` (con motivo) | nombre + (email o teléfono) |
| **Account** | name, domain, sector_code, city, state, lifecycle (`prospecto`, `cliente_activo`, `cliente_recurrente`, `inactivo`), is_key_account, erp_customer_ref | 1:N Contact, Opportunity, Case, OrderReference, EmailMessage | lifecycle derivado de pedidos | dominio único si no es público (gmail, hotmail…) |
| **Contact** | account_id, full_name, email, phone, job_title, is_primary | N:1 Account | activo | email único |
| **Opportunity** | account_id, contact_id, title, type (`estandar`, `formula_personalizada`, `recompra`), stage, est_volume_kg, est_value_mxn, expected_close, lost_reason, owner_id | N:1 Account; 1:N ProductInterest, Quote, Activity | ver pipeline | etapas válidas según tipo |
| **ProductInterest** | opportunity_id, product_id, est_kg, notes (especificación: molienda/malla) | N:1 Opportunity, N:1 Product | — | — |
| **Quote** | opportunity_id, folio (`COT-AAAA-####`), status (`borrador`, `enviada`, `aceptada`, `rechazada`, `vencida`), valid_until, currency=MXN | 1:N QuoteItem | — | folio único |
| **QuoteItem** | quote_id, product_id, qty_kg, packaging (`saco_pp_pead`, `saco_kraft_pe`, `caja_corrugado`), unit_price_mxn | N:1 Quote | — | qty_kg > 0; precio ≥ 0 |
| **OrderReference** | account_id, opportunity_id?, erp_order_id, status (`recibido`, `en_surtido`, `enviado`, `entregado`, `cancelado`), promised_date, delivered_at, total_kg, source_system | N:1 Account | **espejo** del ERP | solo escribe el adaptador |
| **Case** | account_id?, contact_id?, lead_id?, type (`reclamacion_calidad`, `documentacion`, `entrega`, `facturacion`, `otro`), severity (`baja`,`media`,`alta`,`critica`), status (`abierto`, `en_proceso`, `escalado_qms`, `resuelto`, `cerrado`), lot_reference, order_ref, description, owner_id | N:1 Account | lifecycle | `reclamacion_calidad` requiere `lot_reference` para resolver/cerrar |
| **Activity** | type (`llamada`, `correo`, `whatsapp`, `reunion`, `nota`, `sistema`), subject, body, occurred_at, related_type, related_id, actor_id | polimórfica a Lead/Account/Contact/Opportunity/Case | inmutable | — |
| **Task** | title, due_at, status (`pendiente`, `hecha`, `cancelada`), priority, assignee_id, related_type, related_id, origin (`manual`, `auto_lead`, `sugerencia_correo`) | polimórfica | lifecycle | — |
| **EmailMessage** (≈ Communication) | provider, provider_message_id (único), thread_id, from_email, from_name, to, subject, body_text, body_clean, received_at, has_attachments, raw_hash | 1:1 EmailClassification; vínculos opcionales | `ingerido → clasificado` | idempotencia por `provider_message_id` |
| **EmailClassification** | email_id, category, confidence, margin, method (`rules`, `hybrid`, `llm`), scores (JSON), extracted_entities (JSON), suggested_owner_role, suggested_action, crm_link_type/id, review_status (`auto`, `needs_review`, `confirmado`, `corregido`, `aplicado`), review_reason, reviewed_by, final_category, classifier_version | 1:1 EmailMessage | ver flujo del clasificador | — |
| **IntegrationEvent** (outbox) | direction (`in`,`out`), system (`erp`, `email`, `qms`, `wms`), event_type, payload, status (`pendiente`, `procesado`, `error`), attempts, error | — | outbox | — |
| **AuditEvent** | actor_id, action, entity_type, entity_id, before, after, request_id, at | — | inmutable | solo inserción |

**Decisiones de normalización:** *Attachment* se pospone (P1; solo `has_attachments`); *Complaint* se modela como `Case.type=reclamacion_calidad` (una sola entidad de servicio); *Team* es un atributo del usuario (no hay evidencia de estructura de equipos); *PipelineStage* es configuración en código versionada (no tabla) para validar transiciones — ver DECISION_LOG D-07; *Communication* se generaliza en `Activity` + `EmailMessage`.

## 4. Pipeline comercial

**Lead (antes del pipeline):** `nuevo → contactado → calificado → convertido` | `descartado`.
Criterio de calificación (E02, E15): volumen ≥ 500 kg **o** volumen desconocido con sector B2B; ciudad en México. `below_minimum` no descarta automáticamente: lo decide una persona.

**Oportunidad:**

| Etapa (`stage`) | Criterio de entrada | Información requerida | Acción esperada | Criterio de salida | Responsable sugerido | Automatización posible |
|---|---|---|---|---|---|---|
| `requerimiento` | Lead convertido o cuenta existente con necesidad | Producto(s) o descripción, volumen kg estimado | Levantar especificación, empaque, frecuencia | Producto y volumen definidos | Ventas | Tarea "levantar requerimiento" |
| `desarrollo_formula` *(solo fórmula)* | Tipo `formula_personalizada` | Brief (aplicación, perfil de sabor) | Desarrollo prepara propuesta | Muestra lista | Desarrollo/Calidad | Handoff: tarea a rol calidad |
| `muestra_enviada` *(solo fórmula)* | Muestra preparada | Fecha de envío | Seguimiento con el cliente | Respuesta del cliente | Ventas | Recordatorio a 5 días |
| `muestra_aprobada` *(solo fórmula)* | Cliente aprueba | Evidencia de aprobación (actividad) | Preparar cotización | Cotización creada | Ventas | — |
| `cotizacion` | Requerimiento completo (o muestra aprobada) | **≥ 1 Quote** | Enviar cotización | Respuesta del cliente | Ventas | Recordatorio a 3 días |
| `negociacion` | Cliente responde con ajustes | Quote vigente | Ajustar condiciones | Decisión | Ventas (+ Dirección) | — |
| `ganada` | Aceptación | Quote aceptada | Alta en ERP, pedido | Pedido (OrderReference) | Ventas → Administración | `IntegrationEvent` al ERP (simulado) |
| `perdida` | Rechazo / sin respuesta | **`lost_reason` obligatorio** | Registrar motivo | — | Ventas | Recontactar en 90 días (P1) |

Transiciones permitidas (estándar): `requerimiento → cotizacion → negociacion → ganada|perdida`, `cotizacion → ganada|perdida`, cualquier etapa abierta → `perdida`.
Fórmula: `requerimiento → desarrollo_formula → muestra_enviada → muestra_aprobada|desarrollo_formula (iteración) → cotizacion → …`.
**"Cliente recurrente" no es etapa**: es el `lifecycle` de la cuenta (≥ 2 pedidos). La recompra es una oportunidad nueva de tipo `recompra` (entra directo a `cotizacion` si el producto ya existe).

## 5. Arquitectura lógica

```
CLIENTES / PROSPECTOS / USUARIOS INTERNOS
        │  navegador (HTML)            │ formularios web / API
        ▼                              ▼
INTERFAZ CRM (Jinja, rutas /ui)    API REST (/api, JSON)
        └──────────────┬───────────────┘
                       ▼
            SERVICIOS DE APLICACIÓN (app/services)
   leads · accounts · opportunities · activities · tasks · cases · quotes · dashboard · email_pipeline
                       ▼
            DOMINIO CRM (app/models.py + reglas: pipeline.py, dedup.py)
                       ▼
            BASE DE DATOS (SQLAlchemy → SQLite hoy / PostgreSQL después)
                       ▼
     WORKFLOW / AUTOMATIZACIÓN: tarea de primer contacto, sugerencias, recordatorios (P1: scheduler)
                       ▼
     INTEGRATION LAYER (app/integrations): EmailProvider · ErpAdapter · LLMClient · outbox IntegrationEvent
                       ▼
     EMAIL (.eml / mock hoy; Gmail P1) · ERP/WMS/QMS/Facturación (mock hoy)

Transversal: AUTH (sesión) · RBAC (permissions.py) · AUDIT LOG (audit.py) · OBSERVABILITY (logging JSON, request-id, /health)
             CONFIGURATION (config.py, variables de entorno) · BACKUPS (scripts/backup_db.py)
Clasificador: paquete app/classifier desacoplado — no importa modelos de BD; recibe texto + contexto y devuelve un resultado puro.
```

Diagramas: `docs/DIAGRAMAS.md`.
