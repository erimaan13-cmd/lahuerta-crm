# CRM provisional — Empacadora La Huerta (MVP)

MVP de un CRM modular para una distribuidora B2B de especias, granos y condimentos: leads → cuentas/contactos → oportunidades (con subflujo de fórmula personalizada) → cotizaciones → actividades y tareas, más un **clasificador de correos** con bandeja **Needs Review** y un dashboard.

> **Datos 100 % sintéticos.** Ninguna empresa, persona, correo o pedido del repositorio corresponde a clientes reales de Empacadora La Huerta. No hay credenciales reales.

## Requisitos

- Python 3.11+
- `pip install -r requirements.txt`

## Ejecutar (3 comandos)

```bash
pip install -r requirements.txt          # instala FastAPI, SQLAlchemy, Jinja2, Uvicorn, pytest
python -m app.seed                       # crea data/crm.db con datos de demostración (borra la anterior)
python -m uvicorn app.main:app --port 8000   # abre http://127.0.0.1:8000
```

Usuarios de demostración (contraseña `demo1234` para todos, solo demo):

| Correo | Rol |
|---|---|
| admin@demo.local · director@demo.local | Administrador del sistema (todo, incluye **Historial** y **Usuarios**) |
| ventas1@demo.local / ventas2@demo.local | Ventas |
| atencion@demo.local | Atención a clientes |
| calidad@demo.local | Calidad e inocuidad |
| admon@demo.local | Administración |
| direccion@demo.local | Solo lectura |

## Guion de demo (10 minutos)

1. **Dashboard** (`/`): leads, pipeline por etapa, tareas, correos por categoría, Needs Review.
2. **Vertical slice 1** — Leads → "Nuevo lead" con los campos del formulario público → se crea la tarea de primer contacto → registrar una llamada (pasa a *contactado*) → *calificado* → **Convertir** (cuenta + contacto + oportunidad) → crear cotización → mover a *Cotización* → *Ganada* (genera tarea para Administración y evento ERP).
3. **Pipeline** (`/opportunities`): kanban; abrir "Sazonador chipotle-limón" para ver el subflujo de fórmula.
4. **Vertical slice 2** — Correos → abrir "Solicitud de cotización para 3 hoteles" (entidades extraídas, evidencia de reglas) → *Aplicar* `crear_lead`. Luego **Needs Review** → "Reclamación orégano…" → confirmar → *Aplicar* `abrir_caso` (lote incluido). Subir un `.eml` propio desde `/emails`.
5. **Cuenta 360** — "Restaurantes Sabor Norteño": oportunidades, pedidos (referencia ERP simulado), casos, correos e interacciones.
6. **Auditoría** (`/audit`, como admin): quién cambió qué, con antes/después.
7. **Historial total** (como `director@demo.local`): menú **Historial** → filtra por usuario o área; cada clic, cambio, descarga, inicio de sesión y acceso denegado aparece con fecha, usuario, área e IP. **Exportar CSV**. En cualquier lead/cuenta/oportunidad, al final: "Historial de este registro". Menú **Usuarios**: altas, bajas, cambio de área y contraseña (también registrados).
8. **Iteración 2** — en el dashboard, "Recompra pendiente" (Alimentos Procesados del Bajío). En Leads, abrir "Roberto Vela" → **Fusionar en el original**. En la oportunidad "Resurtido trimestral…" → **PDF** de la cotización y **Marcar enviada** (crea la tarea de seguimiento). Las fechas de vencimiento respetan L–V 8–17, hora de Monterrey.

## Pruebas

```bash
python -m pytest -q                                   # 139 pruebas: dominio, clasificador, correo, API, RBAC, historial, CSRF, migraciones
python -m scripts.eval_corpus independiente --sweep   # evaluación honesta del clasificador (ver docs/05)
python scripts/backup_db.py                           # respaldo con marca de tiempo en backups/
python -m app.services.automations                    # revisión de recompra (programable 1 vez al día)
```

## Base de datos y migraciones

- Demo: `python -m app.seed` crea las tablas y las marca en la última migración.
- Instalación nueva o actualización: `alembic upgrade head` (usa `CRM_DATABASE_URL`). Revisiones en `migrations/versions/`.
- Tras cambiar `app/models.py`: `alembic revision --autogenerate -m "..."`, revisar el archivo y correr `alembic check`.

## Configuración (variables de entorno)

| Variable | Default | Uso |
|---|---|---|
| `CRM_DATABASE_URL` | `sqlite:///data/crm.db` | Cambiar a `postgresql+psycopg://…` para PostgreSQL |
| `CRM_SECRET_KEY` | `dev-only-change-me` | **Cambiar** fuera de la demo (firma de sesión) |
| `CRM_CLASSIFIER_THRESHOLD` | `0.60` | Confianza mínima para auto-clasificar |
| `CRM_CLASSIFIER_MIN_MARGIN` | `0.15` | Margen mínimo entre 1ª y 2ª categoría |
| `CRM_LLM_ENABLED` | `false` | Paso híbrido LLM (P1; hoy solo mock en pruebas) |
| `CRM_SUPPLIER_DOMAINS` | dominios demo | Dominios de proveedores para enrutar a Compras |
| `CRM_BUSINESS_TZ` / `_OPEN_HOUR` / `_CLOSE_HOUR` | America/Monterrey · 8 · 17 | Horario hábil para SLA |
| `CRM_REORDER_DEFAULT_DAYS` / `CRM_REORDER_TOLERANCE` | 30 · 0.2 | Regla de recompra |
| `CRM_COMPANY_NAME` | EMPACADORA LA HUERTA | Encabezado del PDF de cotización |

Seguridad: los formularios llevan token CSRF; la API solo acepta `Content-Type: application/json`; 5 intentos fallidos de login bloquean 15 minutos (por IP y correo).

## Estructura

```
app/
  main.py            rutas UI + API, auth, manejo de errores, logging
  models.py          modelo de dominio (SQLAlchemy)
  services/          crm.py · pipeline.py · email_pipeline.py · dashboard.py · business_time.py · quote_pdf.py · automations.py
  classifier/        normalize · rules · extract · engine · llm (puerto) · taxonomy   ← sin dependencia de BD
  integrations/      email_providers.py (EML/Mock/Gmail-stub) · erp.py (mock + sync)
  security.py · permissions.py · audit.py · config.py · seed.py
data/                demo_emails.json · sample_emails/*.eml · eval/ (corpus de evaluación congelados + guía de etiquetado)
migrations/          Alembic (0001 esquema MVP, 0002 iteración 2, 0003 historial encadenado)
scripts/             eval_corpus.py · eval_classifier.py · backup_db.py
docs/                investigación, plan, stack, clasificador, diagramas, decisiones, trazabilidad, backlog, informe
tests/               pytest
```

## Documentación

- `docs/INFORME_FINAL.md` — informe A–Q (empezar aquí)
- `docs/01_INVESTIGACION.md` — Evidence Ledger, organigrama, capability map, procesos, Salesforce, CRM vs ERP/WMS/QMS
- `docs/02_PLAN.md` — requerimientos, NFR, dominio, pipeline, arquitectura
- `docs/03_SELECTOR_DE_STACK.md` · `docs/04_CLASIFICADOR.md` · `docs/05_EVALUACION_CLASIFICADOR.md` · `docs/DIAGRAMAS.md`
- `docs/INFORME_ITERACION_2.md` — qué cambió en la segunda iteración
- `docs/DECISION_LOG.md` · `docs/TRACEABILITY_MATRIX.md` · `docs/BACKLOG.md`
