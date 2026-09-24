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
| AUD-1 | Política de retención del historial de accesos (p. ej. 12–24 meses) y archivo en frío | El historial crece ≈1 fila por clic | S |
| AUD-2 | Verificación de integridad por lotes/puntos de control (hoy recalcula toda la cadena al abrir la página) | Rendimiento con millones de eventos | S |
| AUD-3 | Secuencia de la BD o bloqueo para numerar la cadena con varios procesos (PostgreSQL) | Concurrencia en producción | S |
| AUD-4 | Rol "auditor" (ve historial sin editar datos) si La Huerta lo pide | Separación de funciones | S |

## P2 — congelado durante el MVP

Disponibilidad de inventario desde WMS · apertura de no conformidades en QMS con retorno de estado · portal de clientes · pronóstico de ventas · automatización de marketing · canal retail (visión E12) · modelo ML entrenado con etiquetas acumuladas · borradores de respuesta asistidos (siempre con aprobación humana) · permisos por registro/propietario · multi-idioma en el clasificador.

## Hecho en la iteración 2 (sin depender del cliente)

RF-34 SLA hábil · RF-35 fusión de duplicados · RF-36 PDF y estado de cotización · RF-38 alerta de recompra · evaluación independiente del clasificador (rules-1.0 → 1.1.1) · CSRF · límite de intentos de login · API solo JSON · migraciones con Alembic · hora local en la interfaz.

## Hecho en la iteración 4 — operación interna (23-sep-2026)

Inventario con lotes, bodegas y movimientos · abastecimiento con autorización y recepción · pedidos
que descuentan inventario · mantenimiento de activos con planes por días/km/horas · expedientes de
personal con contratos y alertas · caja chica con comprobante obligatorio · avisos silenciables ·
adjuntos con vencimiento · cuatro roles nuevos · tableros por módulo. Detalle en `06_OPERACION.md`.

## P1 de la operación interna (siguiente iteración)

| ID | Tarea | Por qué |
|---|---|---|
| FAC-1 | Pestaña de facturación por lectura del XML del CFDI | El cliente factura en CONTPAQi; el XML no necesita OCR ni licencias |
| FAC-2 | Conector con el SDK de CONTPAQi Comercial Premium (si esa es su versión) | Existencias y precios en vivo; requiere PC Windows encendida |
| OPE-1 | Tarea programada diaria que ejecute `notifications.generate` | Hoy los avisos se generan a demanda |
| OPE-2 | Adaptador de envío de correo para los avisos | Quedan en cola como `sin_adaptador` |
| OPE-3 | Confirmar con La Huerta: umbral de autorización de compras y si administración autoriza | Hoy solo autoriza `admin` |
| OPE-4 | Recepciones con varios lotes por renglón (tabla de recepciones) | Hoy el renglón guarda el último lote; el rastro completo está en los movimientos |
| OPE-5 | Campos de baja en el expediente (fecha y motivo) para reporte de rotación | Hoy van en notas y bitácora |
| OPE-6 | Aviso de privacidad para empleados y política de uso del sistema | Obligatorio antes de cargar expedientes reales |
| OPE-7 | Migrar lo que hoy llevan en Excel | PENDIENTE de saber qué existe |

## Deuda técnica conocida

- Folios COT/CASO por conteo: posible colisión con concurrencia alta → secuencia en PostgreSQL.
- Reglas del clasificador en español con cobertura básica de inglés; todos los corpus son sintéticos.
- Límite de login en memoria de proceso (no sirve con varios procesos/servidores).
- Feriados propios de La Huerta no configurados (`EXTRA_HOLIDAYS`).
- Los corpus de evaluación ya fueron vistos; el próximo ajuste requiere un corpus independiente nuevo.
- Sesión por cookie firmada sin revocación del lado servidor.
- `IntegrationEvent` de salida no tiene worker que los despache (outbox listo, consumidor pendiente).
- Los archivos adjuntos viven en disco local (`data/uploads`): en la nube hay que montarlos en
  almacenamiento persistente o pasarlos a un bucket antes de exponer el sistema.
- Folios PED/OC/OM por conteo: misma limitación de concurrencia que COT/CASO (secuencia en PostgreSQL).
- Las métricas del tablero recorren las tablas completas; con años de operación conviene agregarlas.
