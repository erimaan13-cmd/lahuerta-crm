# CLAUDE.md — contexto para Claude Code

CRM provisional para Empacadora La Huerta (distribuidor B2B de especias, Guadalupe N.L.). Encargo de Erick (Erii). Responder en español, breve, con el porqué de cada instrucción.

## Comandos

- Instalar: `pip install -r requirements.txt`
- Datos demo: `python -m app.seed` (borra y recrea `data/crm.db`)
- Servidor: `python -m uvicorn app.main:app --port 8000` → http://127.0.0.1:8000 (usuarios en README, contraseña `demo1234`)
- Pruebas: `python -m pytest -q` (deben pasar todas antes de cualquier commit)
- Migraciones: `alembic upgrade head`; tras cambiar `app/models.py` → `alembic revision --autogenerate -m "..."` + revisar + `alembic check`
- Clasificador: `python -m scripts.eval_corpus independiente --sweep`

## Reglas no negociables

1. **Historial total**: toda acción de todo usuario debe quedar en `audit_events` (middleware de acceso + `audit.record()` en cada mutación de servicio). Toda función nueva que cambie datos llama a `record(...)` con el actor. Solo el rol `admin` ve `/audit`. Nunca agregar rutas que editen o borren la bitácora.
2. Sin datos reales de clientes ni credenciales en el repositorio. Datos de prueba: sintéticos y marcados "(DEMO)", dominios `.example`.
3. El CRM no envía, borra, archiva ni responde correos. Las sugerencias del clasificador se aplican solo con clic humano.
4. El CRM no es ERP/WMS/QMS: pedidos, lotes e inventario son referencias (`OrderReference`, `lot_reference`).
5. Clasificador: ajustar reglas solo con `data/eval/dev.json`. Los conjuntos `test_*.json` están congelados por hash; para medir un ajuste nuevo hace falta un corpus independiente nuevo.
6. MODO ENSAYO por defecto. MODO REAL (dinero, publicaciones, envíos, cuentas o sistemas de clientes): preparar y verificar; Erick ejecuta.

## Arquitectura

Rutas (`app/main.py`) → servicios (`app/services/`) → modelos (`app/models.py`). El clasificador (`app/classifier/`) no importa la BD. Integraciones en `app/integrations/` (correo solo lectura, ERP simulado). Decisiones: `docs/DECISION_LOG.md`. Trazabilidad: `docs/TRACEABILITY_MATRIX.md`. Pendientes: `docs/BACKLOG.md`.
