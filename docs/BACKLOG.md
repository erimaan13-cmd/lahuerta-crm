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
| RF-43 | Migrar a PostgreSQL gestionado + migraciones (Alembic) + despliegue con HTTPS | Usuarios reales, respaldos gestionados | M |
| RF-30 | Adaptador Gmail/Graph **solo lectura** (OAuth del cliente) | Ingesta real | M |
| RF-32 | Webhook del formulario web con token y anti-spam | Leads entran solos | S |
| RF-34 | SLA en horario hábil L–V 8–17 (E13) | Hoy se usa hora natural | S |
| RF-40 | Métricas del clasificador desde correcciones (precisión por categoría) y recalibración de umbrales | Medir con datos reales | S |
| RF-31 | Activar LLM en modo híbrido con presupuesto y registro de costo | Correos atípicos / inglés | M |
| RF-35 | Fusión manual de duplicados | Hoy solo se marcan | S |
| RF-36 | PDF de cotización + versionado | Envío al cliente (manual) | M |
| RF-37 | Aprobación de precio especial | Negociación | S |
| RF-38 | Alerta de recompra por inactividad | Clientes recurrentes (E11) | S |
| RF-39 | Adaptador ERP real (clientes, pedidos, crédito) | Sustituir mock | M–L |
| RF-41 | Derechos ARCO: exportar/anonimizar contacto | Privacidad (E16) | S |
| RF-42 | Notificaciones internas (correo/Slack) de tareas vencidas | Seguimiento | S |
| NFR | CSRF tokens en formularios, rate limit de login, rotación de `CRM_SECRET_KEY` | Seguridad antes de exponer a internet | S |
| NFR | Paginación en listas | Rendimiento con volumen real | S |

## P2 — congelado durante el MVP

Disponibilidad de inventario desde WMS · apertura de no conformidades en QMS con retorno de estado · portal de clientes · pronóstico de ventas · automatización de marketing · canal retail (visión E12) · modelo ML entrenado con etiquetas acumuladas · borradores de respuesta asistidos (siempre con aprobación humana) · permisos por registro/propietario · multi-idioma en el clasificador.

## Deuda técnica conocida

- Esquema creado con `create_all` (sin migraciones versionadas).
- Folios COT/CASO por conteo: posible colisión con concurrencia alta → secuencia en PostgreSQL.
- Reglas del clasificador solo en español; el corpus de ajuste es sintético.
- `datetime` en UTC sin zona en la UI (muestra "UTC"); falta presentar hora de Monterrey.
- Sesión por cookie firmada sin revocación del lado servidor.
- `IntegrationEvent` de salida no tiene worker que los despache (outbox listo, consumidor pendiente).
