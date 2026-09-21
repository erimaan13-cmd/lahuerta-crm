# Informe final — MVP CRM provisional · Empacadora La Huerta

> **Actualización (iteración 2):** la cifra del clasificador de la sección J (16/18) fue superada por una evaluación independiente: v1.0 = 53 %, v1.1.1 = 75 % de exactitud. Ver `05_EVALUACION_CLASIFICADOR.md` e `INFORME_ITERACION_2.md`.

Fecha: lunes 21-sep-2026, ≈03:00 h Monterrey (plazo tomado: 21-sep 12:00; el encargo también menciona 22-sep — ver D-01).

**Conclusión:** el MVP es **ejecutable y demostrable**: dos vertical slices completos (lead → cuenta/contacto → oportunidad → cotización → pipeline → actividad/tarea; correo → clasificación → extracción → vínculo CRM → Needs Review → acción humana) y dashboard, con **95 pruebas automatizadas aprobadas**, auditoría, RBAC y datos sintéticos. Lo simulado: ERP, QMS, Gmail y el paso LLM (interfaces definidas y probadas con mocks).

---

## A. Lo que sabemos de la organización

**Hechos verificados (sitio oficial, 21-sep-2026):** importa y distribuye especias, granos, semillas, chiles secos y condimentos para industria alimentaria, hoteles, restaurantes y comedores (E01, E09); venta exclusiva por volumen desde 500 kg, alcance nacional (E02); FSSC 22000 por Global Certification Bureau, vigente a jul-2028, alcance almacenamiento, acondicionamiento y distribución (E03, E04); stock de seguridad con entregas < 72 h (E05); fórmulas personalizadas con equipo especializado (E06); molienda in-house (E07); productos nacionales e importados de proveedores certificados (E08); tres empaques (E10); presentaciones desde 25 kg (E11); fundada en 2015 (E12); un solo correo público `administracion@`, teléfono/WhatsApp, horario L–V 8–17, Guadalupe N.L. (E13); dos formularios de captación con campos concretos (E14, E15); aviso de privacidad con datos de identificación, contacto y patrimoniales (E16).

**Inferencias:** buzón compartido que mezcla ventas, compras, facturación y calidad (fuerte, E17); existe fuerza de ventas industrial y perfil de ingeniería de alimentos (media, fuente secundaria E18); trazabilidad y gestión de quejas exigidas por FSSC 22000 (fuerte, E24); clientes piden fichas técnicas/certificados (débil, E25).

**Recordado (sesiones previas, no verificado hoy):** sin redes sociales salvo LinkedIn; piloto de pauta Google + Meta (E20).

**Desconocido:** tamaño, ERP/sistema contable, proveedor de correo, quién atiende hoy los canales, política de precios y crédito, logística propia o tercerizada, catálogo real y opciones de formulario (E22), razón social completa (E23).

## B. Organigrama / capability map inferido

Ver `01_INVESTIGACION.md §3` y Lucid (organigrama nativo y capability map). Áreas inferidas: Dirección · Comercial (con atención) · Marketing (parcialmente externo) · Administración · Compras/Importaciones · Operaciones (almacén, molienda/empaque, logística) · Calidad e inocuidad (con desarrollo/formulación). Cada nodo tiene evidencia y confianza; **no es oficial**. El capability map clasifica 21 capacidades en A (CRM maestro), B (referencia) o C (sistema externo).

## C. Procesos reconstruidos

Flujo estándar de 15 pasos (lead → contacto SLA → calificación ≥ 500 kg → necesidad → cotización → negociación → cierre → alta en ERP → pedido → surtido → entrega < 72 h → facturación → seguimiento → incidencia → recompra) y subflujo de **fórmula personalizada** (desarrollo → muestra → aprobación/iteración → cotización). Handoffs, datos, automatizaciones y cuellos de botella en `01_INVESTIGACION.md §4`.

## D. Qué pertenece y qué no al CRM

**Maestro en CRM:** leads, cuentas, contactos, oportunidades, cotizaciones (documento comercial), interacciones, tareas, casos con cliente, clasificación de correo, auditoría.
**Solo referencia:** pedidos (`OrderReference`), lote (`lot_reference`), estado de entrega, bandera de crédito (P1).
**Fuera (integración):** inventario, producción/molienda, compras e importaciones, investigación de calidad/CAPA, facturación/CFDI. Matriz completa en `01_INVESTIGACION.md §6`.

## E. Arquitectura elegida

Monolito modular en capas: UI (Jinja) + API REST → servicios → dominio → SQLAlchemy (SQLite hoy, PostgreSQL después) → workflow (tareas automáticas) → capa de integración (EmailProvider, ErpAdapter, outbox `IntegrationEvent`). Transversal: sesión firmada, RBAC, auditoría append-only, logs JSON con request-id, `/health`, configuración por entorno, script de respaldo. Clasificador en paquete **sin dependencia de BD**.

## F. Resultado de /selector-de-stack

Tres alternativas con 17 criterios ponderados: **FastAPI + SQLAlchemy + SQLite→PostgreSQL 83.6 %** · Supabase + Next.js/Vercel 76.4 % · CRM SaaS + Zapier 54.5 %. Se eligió la primera por plazo, pruebas locales, $0 y portabilidad; Supabase/PostgreSQL queda como destino de migración P1. Detalle en `03_SELECTOR_DE_STACK.md`.

## G. Modelo de datos

18 tablas: users, sectors, products, accounts, contacts, leads, opportunities, product_interests, quotes, quote_items, order_references, cases, activities, tasks, email_messages, email_classifications, integration_events, audit_events. Decisiones de normalización: Complaint → `Case.type`; "cliente recurrente" es `Account.lifecycle`, no etapa; etapas como configuración versionada. `02_PLAN.md §3`.

## H. Diagramas

8 diagramas en Mermaid versionado (validados) y en Lucid: system context, organigrama, capability map, customer journey, arquitectura lógica, ERD, flujo del clasificador, integration map. Enlaces en `DIAGRAMAS.md`.

## I. Funciones implementadas (funcionan y están probadas)

Captura de leads (UI + API) con los campos de los formularios públicos · deduplicación (email exacto; teléfono/dominio como posible duplicado; dominios públicos excluidos) · bandera bajo mínimo 500 kg · tarea automática de primer contacto · estados de lead con reglas · conversión a cuenta/contacto/oportunidad reutilizando cuenta por dominio · oportunidades de tipo estándar/fórmula/recompra · pipeline con transiciones validadas y subflujo de fórmula · cotizaciones con partidas, empaques y totales · ganada → cuenta cliente + tarea Administración + evento ERP · actividades y línea de tiempo · tareas · casos con lote obligatorio y escalamiento QMS (evento) · búsqueda global y filtros · vista 360 de cuenta · ingesta de correo (.eml, JSON, API, subida manual) · clasificador · extracción · vinculación · Needs Review · aplicar sugerencia · dashboard · RBAC (6 roles) · auditoría con antes/después · exportación JSON · sincronización de pedidos desde ERP simulado · respaldo.

## J. Clasificador de correos

12 categorías (se añadió **DOCUMENTACION_CALIDAD**; "cliente existente" pasó de categoría a dimensión de vínculo). Método: reglas ponderadas + contexto del remitente; puerto LLM híbrido desactivado. **Umbral 0.60, margen 0.15; reclamaciones y "Otro" siempre a revisión.** Ninguna acción sin clic humano; nunca responde ni modifica buzones. En el corpus sintético: 16/18 correctos; 14/14 auto-clasificados correctos; los 2 errores cayeron en Needs Review (cifra optimista: corpus de ajuste). `04_CLASIFICADOR.md`.

## K. Pruebas realizadas

95 pruebas pytest (todas aprobadas, también en entorno limpio con `requirements.txt`): leads y deduplicación, conversión, pipeline y cotizaciones, fórmula, actividades, tareas, casos, búsqueda/filtros, clasificador (11 categorías + ambiguos + inglés + LLM mock), extracción, normalización, ingesta idempotente, vinculación, Needs Review, aplicar sugerencias, RBAC (matriz), sesión manipulada, auditoría, errores 401/403/404/422, request-id, ERP sync, E2E por API. Además: recorrido de la demo por formularios HTML y capturas de pantalla revisadas. La verificación encontró y corrigió **2 bugs reales** de relaciones en memoria y 2 menores (`TRACEABILITY_MATRIX.md`).

## L. Qué funciona realmente

Todo lo listado en I, ejecutándose localmente con `python -m app.seed` + `uvicorn`, con datos sintéticos.

## M. Qué está simulado / mockeado

ERP (pedidos, clientes) → `MockErpAdapter` · QMS → solo evento en outbox · Gmail → `GmailProvider` no implementado (EML/JSON en su lugar) · LLM → `MockLLMClient` en pruebas · catálogo de productos, sectores, precios, clientes y correos → sintéticos · despacho de eventos de salida → no hay worker.

## N. Qué no pudo verificarse

Opciones reales de los formularios; contenido de LinkedIn (robots.txt); vacantes activas; organigrama real; sistemas que usa La Huerta; volumen de correos; desempeño del clasificador con correos reales; acomodo visual de los diagramas en Lucid.

## O. Riesgos y deuda técnica

Clasificador ajustado a corpus sintético y solo en español · SQLite sin migraciones versionadas · folios por conteo (colisión con concurrencia) · sin CSRF ni rate-limit (no exponer a internet aún) · SLA en horas naturales · sesión sin revocación · outbox sin consumidor · dependencia de decisiones de La Huerta aún desconocidas (correo, ERP). Mitigaciones en `BACKLOG.md`.

## P. Backlog P1/P2

P1: PostgreSQL + Alembic + despliegue HTTPS; Gmail/Graph solo lectura; webhook de formulario; SLA hábil; métricas y recalibración del clasificador; LLM híbrido con presupuesto; fusión de duplicados; PDF de cotización; aprobaciones de precio; alerta de recompra; ERP real; ARCO; notificaciones; CSRF/rate-limit. P2: WMS, QMS bidireccional, portal, pronóstico, marketing automation, retail, ML entrenado, borradores asistidos. `BACKLOG.md`.

## Q. Próxima iteración recomendada

1. Validar con La Huerta las 8 preguntas de `BACKLOG.md` (sobre todo **proveedor de correo y ERP**).
2. Con 50–100 correos reales anonimizados, medir el clasificador y recalibrar umbrales.
3. Migrar a PostgreSQL con Alembic y desplegar con HTTPS + CSRF antes de dar acceso a usuarios reales.
