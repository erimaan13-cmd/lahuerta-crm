# 03 · Resultado de /selector-de-stack

**Conclusión en una línea:** para el MVP, **Python 3.11 + FastAPI + SQLAlchemy 2 + SQLite (portable a PostgreSQL) + plantillas Jinja**, con clasificador **híbrido: reglas deterministas hoy + puerto LLM desactivado**; migración planificada a PostgreSQL (Supabase u otro) en P1.

## Contexto reconstruido (6 preguntas)

1. **Qué y para quién:** CRM provisional para Empacadora La Huerta; demo para el cliente → base para seguir construyendo (encargo con continuidad).
2. **Fase:** prototipo funcional (datos sintéticos). Datos reales y despliegue llegan después.
3. **Nivel técnico de Erick:** programa apoyado en IA, sin equipo → código simple, un solo lenguaje, sin frontend separado.
4. **Presupuesto:** cero gasto nuevo.
5. **Ya disponible:** ver tabla.
6. **Documentos del proyecto:** ninguno fija un stack para este CRM (VERIFICADO: lista de docs del proyecto, 21-sep-2026).

## Inventario (estado según la regla de oro)

| Recurso | Estado | Evidencia (21-sep-2026) | Costo | ¿Ahora? |
|---|---|---|---|---|
| Python 3.11.15 + FastAPI 0.141.1 + SQLAlchemy 2.0.54 + Jinja2 3.1.6 + Uvicorn 0.46.0 + pytest 9.1.1 | **Probado** (instalado y ejecutado en el contenedor) | `python -c import …` | $0 | Sí |
| SQLite 3.45.1 | **Probado** | `sqlite3.sqlite_version` | $0 | Sí |
| Supabase (PostgreSQL 17 gestionado) | **Probado** (conector responde: 1 proyecto `ACTIVE_HEALTHY` creado 17-sep-2026) | `list_projects` | Plan actual DESCONOCIDO | No (P1) — el proyecto existente parece de otro trabajo; no mezclar |
| Vercel | **Mencionado/conectado**, no probado para este caso | lista de herramientas | — | No |
| Lucid | **Probado** (búsqueda en la cuenta respondió) | `search` | $0 incremental | Sí, para diagramas |
| Gmail (conector) | Conectado a la cuenta **de Erii**, no de La Huerta | lista de herramientas | — | **No**: no hay autorización sobre el buzón de La Huerta |
| API de LLM para el clasificador | **Pendiente**: no hay clave propia del proyecto | — | Por uso | No (P1) |

## Matriz ponderada (17 criterios, peso 1–3, puntuación 1–5)

A = FastAPI + SQLAlchemy + SQLite→Postgres (monolito modular) · B = Supabase (Postgres + Auth + RLS) + Next.js en Vercel · C = CRM SaaS gratuito (p. ej. HubSpot Free) + automatizador (Zapier/Make) + clasificador aparte

| # | Criterio | Peso | A | B | C |
|---|---|---|---|---|---|
| 1 | Construir el MVP en el plazo | 3 | 5 | 2 | 3 |
| 2 | Costo inicial | 2 | 5 | 4 | 4 |
| 3 | Facilidad de mantenimiento | 2 | 4 | 3 | 4 |
| 4 | Escalabilidad | 2 | 3 | 5 | 3 |
| 5 | Velocidad de desarrollo asistido por Claude | 3 | 5 | 4 | 1 |
| 6 | Integración con correo | 2 | 4 | 3 | 3 |
| 7 | Integración futura ERP/WMS/QMS | 2 | 4 | 4 | 2 |
| 8 | Autenticación y RBAC | 2 | 3 | 5 | 3 |
| 9 | Base de datos relacional | 2 | 4 | 5 | 2 |
| 10 | Auditoría | 2 | 5 | 4 | 2 |
| 11 | Automatización | 1 | 3 | 4 | 5 |
| 12 | APIs | 2 | 5 | 4 | 3 |
| 13 | Despliegue | 1 | 2 | 5 | 5 |
| 14 | Migración futura | 2 | 5 | 4 | 2 |
| 15 | Vendor lock-in (5 = bajo) | 2 | 5 | 3 | 1 |
| 16 | Observabilidad | 1 | 3 | 3 | 2 |
| 17 | Seguridad | 2 | 3 | 4 | 4 |
| | **Total (máx. 165)** | 33 | **138 (83.6 %)** | 126 (76.4 %) | 90 (54.5 %) |

Razones principales (INFERIDO salvo lo marcado):
- **A gana por plazo, pruebas y portabilidad**: todo se ejecuta y prueba aquí mismo (VERIFICADO), sin cuentas ni secretos; el modelo SQLAlchemy migra a PostgreSQL cambiando `DATABASE_URL`.
- **B es la mejor opción de escala** (Auth + RLS + backups gestionados), pero exige configurar claves, un proyecto nuevo y despliegue antes de la demo → riesgo de plazo. Queda como **destino de migración P1**.
- **C** resuelve rápido la parte CRM genérica, pero el clasificador y la trazabilidad quedarían fuera, con dependencia alta y datos difíciles de migrar; y no puedo operar la cuenta.

## Recomendación principal

**A**, porque es la única que permite terminar hoy un flujo completo **y probado** sin gastar ni introducir credenciales, sin sacrificar el modelo de datos.

**Alternativa (cuándo cambiar):** pasar la persistencia y la autenticación a **B (PostgreSQL gestionado + Auth)** cuando haya usuarios reales de La Huerta o se necesite acceso fuera de la red local. La capa de servicios no cambia.

## Clasificador: reglas vs LLM vs ML tradicional vs híbrido

| Opción | Pros | Contras | Veredicto MVP |
|---|---|---|---|
| Reglas (palabras clave ponderadas + contexto del remitente) | Determinista, explicable, $0, testeable, sin datos de entrenamiento | Recall limitado en redacción libre | **Base del MVP** |
| LLM | Mejor comprensión y extracción de texto libre | Costo por correo, latencia, requiere clave y política de datos, no determinista | **Puerto definido, desactivado** (P1) |
| ML tradicional (TF-IDF + regresión) | Barato, rápido | **No hay corpus etiquetado real** | Descartado hasta acumular etiquetas desde Needs Review |
| **Híbrido** reglas → LLM solo en baja confianza | Costo controlado, explicabilidad + cobertura | Dos componentes | **Arquitectura objetivo**; en el MVP el paso LLM es un mock |

## Lo que descarto hoy y por qué

- Frontend separado (React/Next): duplica la capa de presentación sin beneficio para una demo; Jinja basta.
- Colas/Celery/Redis: volumen desconocido y bajo; la ingesta es un comando o endpoint.
- Nuevo proyecto Supabase: gasto de configuración y riesgo de mezclar con el proyecto existente.
- Gmail real: sin autorización sobre el buzón de La Huerta (regla 11 del encargo).

## Pendientes de verificación

Si La Huerta usa Google Workspace o Microsoft 365 · si tiene ERP/sistema contable y cuál · volumen diario de correos · dónde se alojaría (nube vs local).

## Acción concreta de Erick

Preguntar a La Huerta: **"¿Qué proveedor de correo y qué sistema de facturación/ERP usan hoy?"** — define los dos primeros adaptadores reales.

## Fichas de biblioteca

| Nombre | Función | Fuente y fecha | Estado | Disponibilidad | Requisitos | Costo | Aplicación | Prioridad |
|---|---|---|---|---|---|---|---|---|
| FastAPI | Framework web/API Python | pypi, 21-sep-2026 | Probado 0.141.1 | Sí | Python ≥3.9 | $0 (MIT) | API + UI del CRM | Alta |
| SQLAlchemy | ORM / SQL portable | pypi, 21-sep-2026 | Probado 2.0.54 | Sí | — | $0 (MIT) | Modelo de datos | Alta |
| SQLite | BD embebida | stdlib, 21-sep-2026 | Probado 3.45.1 | Sí | — | $0 | Persistencia MVP | Alta |
| Supabase | Postgres gestionado + Auth | conector, 21-sep-2026 | Probado (listado) | Cuenta de Erii | Proyecto dedicado | Plan DESCONOCIDO | Migración P1 | Media |
| Lucid | Diagramas | conector, 21-sep-2026 | Probado | Cuenta de Erii | — | Plan actual | Diagramas del CRM | Media |
