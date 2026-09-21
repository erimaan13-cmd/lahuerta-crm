# Entrega técnica — CRM La Huerta (para revisión de Abraham / TI24)

Fecha: 21-sep-2026 · Preparado por: Erick (con Claude) · Estado: **MVP funcional con datos sintéticos, no desplegado**

## En 30 segundos

CRM web para Empacadora La Huerta: leads → cuentas/contactos → oportunidades → cotizaciones (PDF) → casos de calidad, más un **clasificador de correos** que solo *sugiere* (nada se ejecuta sin clic humano) y un **historial total auditable** (cada acción de cada usuario, cadena SHA-256, solo visible para administradores).

Python 3.11+ · FastAPI · SQLAlchemy 2 · SQLite (listo para PostgreSQL vía Alembic) · plantillas Jinja (sin frontend JS) · 139 pruebas pytest.

**Qué te pido:** revisar, auditar y decidir cómo y dónde se pone en producción. Las decisiones de negocio y de infraestructura de la última sección son tuyas.

## Arrancarlo (5 minutos)

```bash
git clone <URL-del-repo> && cd lahuerta-crm
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q                                # 139 deben pasar
python -m app.seed                                 # datos DEMO (borra data/crm.db)
python -m uvicorn app.main:app --port 8000         # http://127.0.0.1:8000
```

Usuario administrador demo: `director@demo.local` / `demo1234` (demo local; no existe fuera de tu máquina). Guion de demo de 10 min en `README.md`.

**Con Claude Code:** abre la carpeta y ejecuta `claude`. Lee automáticamente `CLAUDE.md` (raíz del repo) con los comandos y las reglas no negociables. Si cambias una regla, cámbiala ahí para que la siga cualquier Claude que trabaje en el proyecto.

## Mapa del código

| Dónde | Qué |
|---|---|
| `app/main.py` | Rutas UI + API, middleware (request id, CSRF, JSON-only, registro de accesos), login |
| `app/services/` | Lógica de negocio. `crm.py` (leads, conversión, cotizaciones, casos, fusión), `pipeline.py` (etapas y transiciones), `email_pipeline.py`, `users.py`, `business_time.py` (SLA hábil Monterrey) |
| `app/models.py` | 18 tablas |
| `app/audit.py` | Bitácora: `record()`, cadena de hash, bloqueo de UPDATE/DELETE en el ORM, `verify_chain()` |
| `app/permissions.py` · `app/security.py` | RBAC por rol · PBKDF2 + cookie de sesión firmada con HMAC |
| `app/classifier/` | Reglas ponderadas + extracción; **no importa la BD**; puerto LLM desactivado |
| `app/integrations/` | Correo (EML/Mock; Gmail = stub) y ERP **simulado** |
| `migrations/` | Alembic 0001–0003 |
| `tests/` | 139 pruebas: dominio, API, RBAC, CSRF, historial, migraciones |

Capas: rutas → servicios → modelos. Toda mutación pasa por un servicio que llama a `audit.record()`.

## Dónde leer el porqué

- `docs/INFORME_FINAL.md`: informe completo A–Q. Empieza aquí.
- `docs/DECISION_LOG.md`: 32 decisiones con alternativas y consecuencias.
- `docs/02_PLAN.md`: requerimientos, modelo de dominio, arquitectura.
- `docs/03_SELECTOR_DE_STACK.md`: por qué FastAPI y no Supabase + Next/Vercel.
- `docs/05_EVALUACION_CLASIFICADOR.md`: métricas honestas.
- `docs/BACKLOG.md`: pendientes P1/P2 y deuda técnica.
- `docs/01_INVESTIGACION.md`: evidencia pública sobre La Huerta.

## Qué auditar primero (sugerencia, en orden)

1. **Seguridad de sesión y acceso** (`security.py`, `main.py`):
   - La cookie firmada no tiene revocación del lado servidor.
   - CSRF por doble envío.
   - El límite de login vive **en memoria**, así que no sirve con varios procesos.
   - Faltan cabeceras CSP y HSTS.
2. **Bitácora** (`audit.py`):
   - La numeración de la cadena no es segura con varios procesos escribiendo a la vez. Con PostgreSQL necesita una secuencia o un bloqueo (AUD-3).
   - `verify_chain()` recalcula todo (AUD-2).
   - Falta política de retención (AUD-1).
3. **Migración a PostgreSQL**:
   - Correr `alembic upgrade head` contra una BD vacía.
   - Folios COT/CASO por conteo: riesgo de colisión, conviene una secuencia.
4. **RBAC** (`permissions.py`): los permisos son por rol, no por registro. Todo vendedor ve todas las cuentas. ¿Es aceptable para La Huerta?
5. **Clasificador**:
   - Aciertos: 75 % en el corpus independiente y 87 % en el holdout. Todos los corpus son sintéticos.
   - La precisión real es desconocida hasta tener correos reales.
   - Reclamaciones de calidad y "otro" van **siempre** a revisión humana.

## Riesgos y límites conocidos

- **Datos:** 100 % sintéticos ("(DEMO)", dominios `.example`). No hay credenciales reales en el repo; `.env` y `data/crm.db` están en `.gitignore`.
- **Correo:** el CRM **no envía, borra, archiva ni responde** correos (regla de diseño, D-12/D-23).
- **Alcance:** no es ERP/WMS/QMS. Pedidos y lotes son solo referencias.
- **Servidor:** es un servidor Python de proceso largo. **Vercel no es el destino natural**: requeriría adaptarlo a funciones serverless, y su plan Hobby es no comercial. Encajan mejor un PaaS con contenedores (Render, Railway, Fly.io) o un VPS, junto con PostgreSQL gestionado. Precios por verificar.
- **Sin CI** todavía. Sugerido: GitHub Actions que corra `pytest` y `alembic check` en cada push.

## Para producción falta (resumen de `BACKLOG.md`)

1. PostgreSQL gestionado, HTTPS y dominio.
2. Variables de entorno: `CRM_DATABASE_URL`, un `CRM_SECRET_KEY` nuevo y aleatorio.
3. Respaldos automáticos y un entorno de staging.
4. Usuarios reales y catálogo real; borrar los datos DEMO (no correr `app.seed` en producción).
5. Aviso de privacidad y acuerdo de tratamiento de datos con La Huerta.
6. Integraciones que requieren autorización de La Huerta: lectura de correo (Gmail/Graph OAuth), webhook del formulario web, ERP.

## Decisiones que te tocan

**Infraestructura y propiedad**

1. ¿A nombre de quién quedan repo, hosting, BD y dominio? Principio acordado: producción bajo TI24. ¿Quién paga?
2. Hosting y presupuesto mensual. ¿Mantener el stack actual o migrar a otro?
3. ¿Dominio o subdominio? ¿Quién configura el DNS?
4. ¿Proyecto independiente o módulo dentro del CRM de TI24?

**Con La Huerta**

5. ¿Aprobaron un piloto? ¿Quién es el contacto?
6. ¿Qué correo usan (Google/Microsoft)? ¿Tienen ERP? ¿Cuál?
7. Usuarios reales por área y quiénes serán administradores.
8. Acuerdo de datos y aviso de privacidad: quién lo redacta y quién lo firma.
9. Retención del historial de accesos. Sugerido: 12–24 meses.

**Operación**

10. Mantenimiento: quién, tiempos de respuesta y precio. Reparto de trabajo con Erick.
11. Flujo de cambios: ramas y pull requests, quién aprueba, pruebas obligatorias antes de fusionar.
12. ¿Qué hallazgos de tu auditoría bloquean el piloto y cuáles pueden ir al backlog?

Deja tus hallazgos como *Issues* en GitHub, o como comentarios en un *pull request*, para que quede historial.
