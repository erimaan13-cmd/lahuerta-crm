# Backlog posterior al MVP

## Validaciones con La Huerta (bloquean decisiones, antes de programar P1)

1. ¿Qué proveedor de correo usan (Google Workspace, Microsoft 365, otro)? → define RF-30.
2. ¿Tienen ERP / sistema contable? ¿Cuál? → define RF-39.
3. ¿Quién atiende hoy formularios, WhatsApp y `administracion@`? → roles reales y enrutamiento.
4. Lista real de productos, sectores y opciones de los formularios (E22).
5. Política de precios, aprobaciones y crédito.
6. Entrega propia o tercerizada; zonas de cobertura.
7. Volumen diario de correos y de leads (dimensiona la necesidad de LLM y colas).
8. Tratamiento de datos personales para usar un LLM externo (aviso de privacidad, E16).

## P1 — siguiente iteración

| ID | Tarea | Por qué | Esfuerzo |
|---|---|---|---|
| RF-43 | Migrar a PostgreSQL gestionado (las migraciones Alembic ya existen) + despliegue con HTTPS | Usuarios reales, respaldos gestionados | M |
| RF-30 | Adaptador Gmail/Graph **solo lectura** (OAuth del cliente) | Ingesta real | M |
| RF-32 | Webhook del formulario web con token y anti-spam | Leads entran solos | S |
| RF-40b | Tablero de métricas del clasificador a partir de las correcciones en Needs Review (la evaluación offline ya existe) | Medir con datos reales | S |
| CLS-2 | Recall de LEAD_NUEVO / PEDIDO / CALIDAD coloquial; desempate PEDIDO > SEGUIMIENTO; spam tipo SAT — **con corpus independiente nuevo** | Hallazgos de `05_EVALUACION_CLASIFICADOR.md` | M |
| AUT-1 | Programador diario para `run_reorder_check` y tareas vencidas | Hoy es bajo demanda | S |
| RF-31 | Activar LLM en modo híbrido con presupuesto y registro de costo | Correos atípicos / inglés | M |
| RF-36b | Versionado de cotizaciones (v2, v3 de un mismo folio) | Negociación | S |
| RF-37 | Aprobación de precio especial | Negociación | S |
| RF-39 | Adaptador ERP real (clientes, pedidos, crédito) | Sustituir mock | M–L |
| RF-41 | Derechos ARCO: exportar/anonimizar contacto | Privacidad (E16) | S |
| RF-42 | Notificaciones internas (correo/Slack) de tareas vencidas | Seguimiento | S |
| NFR | Rotación de `CRM_SECRET_KEY`, cabeceras de seguridad (CSP, HSTS), límite de login en almacenamiento compartido | Antes de exponer a internet | S |
| NFR | Paginación en listas | Rendimiento con volumen real | S |

## P2 — congelado durante el MVP

Disponibilidad de inventario desde WMS · apertura de no conformidades en QMS con retorno de estado · portal de clientes · pronóstico de ventas · automatización de marketing · canal retail (visión E12) · modelo ML entrenado con etiquetas acumuladas · borradores de respuesta asistidos (siempre con aprobación humana) · permisos por registro/propietario · multi-idioma en el clasificador.

## Hecho en la iteración 2 (sin depender del cliente)

RF-34 SLA hábil · RF-35 fusión de duplicados · RF-36 PDF y estado de cotización · RF-38 alerta de recompra · evaluación independiente del clasificador (rules-1.0 → 1.1.1) · CSRF · límite de intentos de login · API solo JSON · migraciones con Alembic · hora local en la interfaz.

## Deuda técnica conocida

- Folios COT/CASO por conteo: posible colisión con concurrencia alta → secuencia en PostgreSQL.
- Reglas del clasificador en español con cobertura básica de inglés; todos los corpus son sintéticos.
- Límite de login en memoria de proceso (no sirve con varios procesos/servidores).
- Feriados propios de La Huerta no configurados (`EXTRA_HOLIDAYS`).
- Los corpus de evaluación ya fueron vistos; el próximo ajuste requiere un corpus independiente nuevo.
- Sesión por cookie firmada sin revocación del lado servidor.
- `IntegrationEvent` de salida no tiene worker que los despache (outbox listo, consumidor pendiente).
