# TRACEABILITY_MATRIX

`EVIDENCIA → PROCESO → REQUERIMIENTO → ENTIDAD → MÓDULO → PRUEBA`
Evidencias: `docs/01_INVESTIGACION.md §2`. Requerimientos: `docs/02_PLAN.md §1`. Pruebas en `tests/` (**139 casos, todos pasan** — iteración 3, 21-sep-2026). Estado: ✅ implementado y probado · 🟡 simulado/mock probado · ⬜ solo diseño.

| Evidencia | Proceso | Requerimiento | Entidad | Módulo | Prueba(s) | Estado |
|---|---|---|---|---|---|---|
| E14, E15, E20 | Lead (captura) | RF-01 | Lead, Sector | `services/crm.create_lead`, `POST /api/leads`, `/leads` | `test_leads::test_create_lead_with_form_fields_and_first_contact_task`, `::test_create_lead_validation_errors` (8 casos negativos), `test_api_security_audit::test_end_to_end_vertical_slice_1_via_api` | ✅ |
| E17, E19 | Lead (deduplicación) | RF-02 | Lead, Contact, Account | `crm.create_lead` (D-13, D-14) | `test_leads::test_dedup_exact_email_does_not_create_new_lead`, `::test_possible_duplicate_by_phone_and_domain`, `::test_public_domain_is_not_duplicate_signal` | ✅ |
| E02, E15 | Calificación | RF-03 | Lead | `crm.change_lead_status` | `test_leads::test_below_minimum_flag`, `::test_status_transitions`, `::test_qualify_requires_company` | ✅ |
| E01 | Conversión lead → cliente | RF-04 | Account, Contact, Opportunity, ProductInterest | `crm.convert_lead` | `test_leads::test_convert_*` (5 pruebas), `test_api_security_audit::test_convert_permission` | ✅ |
| E06, E11 | Oportunidad | RF-05 | Opportunity, ProductInterest | `crm.create_opportunity` | `test_pipeline::test_create_opportunity_validations` | ✅ |
| E06, E14 | Pipeline / fórmula | RF-06 | Opportunity | `services/pipeline.py`, `crm.change_stage` | `test_pipeline::test_invalid_transition_rejected`, `::test_lost_requires_reason_and_closes`, `::test_formula_subflow_with_iteration`, `::test_stage_change_via_api` | ✅ |
| E05, E14 | Ganada → pedido (handoff) | RF-06, RF-22 | IntegrationEvent, Task | `crm.change_stage` (outbox) | `test_pipeline::test_won_updates_account_emits_integration_event_and_admin_task` | 🟡 evento generado; ERP real no existe |
| E13 | Interacciones | RF-07 | Activity | `crm.log_activity`, `_timeline.html` | `test_activities_cases_search::test_activity_on_new_lead_marks_contacted_and_closes_first_contact_task`, `::test_activity_validation` | ✅ |
| E14 | Seguimiento / SLA | RF-08 | Task | `crm.create_lead` (auto), `crm.create_task/complete_task` | `test_leads::test_create_lead_with_form_fields_and_first_contact_task`, `test_activities_cases_search::test_task_lifecycle` | ✅ (horas hábiles desde la iteración 2, RF-34) |
| — | Búsqueda y filtros | RF-09 | Lead, Account, Contact, Opportunity | `crm.search`, `crm.filter_leads` | `test_activities_cases_search::test_search_by_name_company_email_phone_and_short_query`, `::test_filters` | ✅ |
| E17 | Ingesta de correo | RF-10 | EmailMessage | `integrations/email_providers.py`, `email_pipeline.ingest` | `test_email_pipeline::test_ingest_is_idempotent_and_counts_errors`, `::test_eml_parsing_html_attachment_and_directory`, `::test_gmail_provider_is_explicitly_not_implemented` | ✅ EML/mock · ⬜ Gmail |
| — | Normalización | RF-11 | EmailMessage.body_clean | `classifier/normalize.py` | `test_classifier::test_normalization_strips_html_and_quoted_history` | ✅ |
| E17, E03, E06, E08 | Clasificación con confianza | RF-12 | EmailClassification | `classifier/rules.py`, `engine.py` | `test_classifier::test_categories` (11 categorías), `::test_known_sender_is_never_new_lead`, `::test_hybrid_llm_only_called_when_uncertain`, `::test_llm_disabled_by_default` | ✅ reglas · 🟡 LLM (mock) |
| E09–E11 | Extracción de entidades | RF-13 | EmailClassification.extracted_entities | `classifier/extract.py` | `test_classifier::test_extraction_fields`, `::test_extraction_edge_cases` | ✅ |
| — | Vinculación CRM | RF-14 | EmailClassification.crm_link* | `email_pipeline.resolve_sender/link_references` | `test_email_pipeline::test_link_to_contact_and_opportunity_by_quote_folio`, `::test_link_by_corporate_domain_when_sender_unknown` | ✅ |
| — | Enrutamiento y sugerencia | RF-15 | EmailClassification.suggested_* | `classifier/taxonomy.py`, `email_pipeline.apply_suggestion` | `test_classifier::test_new_sender_quote_suggests_create_lead_known_sender_suggests_task`, `test_email_pipeline::test_review_then_apply_create_lead`, `::test_apply_task_for_order_email`, `::test_supplier_email_routed_outside_crm`, `::test_open_case_without_link_fails` | ✅ |
| E24 | Revisión humana | RF-16 | EmailClassification.review_status | `email_pipeline.review`, `/emails/needs-review` | `test_classifier::test_no_signal_goes_to_needs_review_as_other`, `::test_quality_claim_always_needs_review_even_with_high_confidence`, `::test_ambiguous_mixed_email_needs_review_by_margin`, `::test_unsupported_language_is_not_forced_into_a_category`, `test_email_pipeline::test_review_invalid_category` | ✅ |
| — | Contrato de salida del clasificador | RF-12..15 | — | `GET /api/emails` | `test_email_pipeline::test_api_email_contract` | ✅ |
| — | Dashboard | RF-17 | (agregados) | `services/dashboard.py`, `/` | `test_api_security_audit::test_end_to_end_vertical_slice_1_via_api` (métricas), `::test_ui_pages_render_for_each_role` | ✅ |
| E03, E24 | Reclamación / caso | RF-18 | Case, IntegrationEvent | `crm.create_case/change_case_status` | `test_activities_cases_search::test_quality_claim_requires_lot_to_resolve_and_escalates_to_qms`, `::test_case_invalid_type_and_severity`, `test_email_pipeline::test_quality_claim_opens_case_with_lot_after_human_confirmation` | ✅ · 🟡 QMS (evento) |
| E10, E14 | Cotización | RF-19 | Quote, QuoteItem | `crm.create_quote` | `test_pipeline::test_quotation_stage_requires_quote`, `::test_quote_item_validation`, `::test_empty_quote_rejected` | ✅ (PDF y estados en iteración 2, RF-36) |
| — | Autenticación / RBAC | RF-20, RNF-01..03 | User | `security.py`, `permissions.py`, `main.require` | `test_api_security_audit::test_unauthenticated`, `::test_bad_password_and_tampered_cookie`, `::test_rbac_matrix` (8 casos), `::test_convert_permission` | ✅ |
| — | Auditoría | RF-21, RNF-05 | AuditEvent | `audit.py` | `test_api_security_audit::test_audit_trail_records_actor_and_diff`, `::test_audit_is_append_only_no_mutation_routes` | ✅ |
| E05 | Pedidos (referencia ERP) | RF-22 | OrderReference, IntegrationEvent | `integrations/erp.py` | `test_api_security_audit::test_erp_sync_idempotent_lifecycle_and_unmatched` | 🟡 adaptador mock |
| — | Manejo de errores | RNF-07 | — | handlers en `main.py` | `test_api_security_audit::test_errors_are_json_with_proper_codes`, `::test_ui_domain_error_renders_page` | ✅ |
| — | Observabilidad | RNF-09 | — | middleware request-id, logs JSON, `/health` | `test_api_security_audit::test_health_and_request_id` | ✅ básico |
| — | Datos de demostración | RF-23 | todas | `app/seed.py`, `data/` | ejecución de `python -m app.seed` (18 correos, 1 duplicado, 1 malformado) | ✅ |
| E16 | Portabilidad / ARCO | RNF-11, RF-41 | — | `GET /api/export` | `test_rbac_matrix` (permiso) | ✅ exportación · ⬜ ARCO |

## Hallazgos de la verificación (bugs reales encontrados y corregidos)

1. **Relación en memoria desactualizada al cotizar** (`opp.quotes` vacío tras crear cotización en la misma sesión) → una oportunidad con cotización no podía pasar a "Cotización". Detectado por `test_quotation_stage_requires_quote`. Corrección: `opp.quotes.append(q)`.
2. **Mismo defecto en la sincronización ERP**: el ciclo de vida no subía a `cliente_recurrente`. Detectado por `test_erp_sync_idempotent_lifecycle_and_unmatched`. Corrección: `acc.orders.append(ref)`.
3. **Checkbox "Crear oportunidad" desmarcado** se interpretaba como marcado (revisión de código). Corregido.
4. Mensaje 404 con concordancia de género incorrecta ("Oportunidad no encontrado"). Corregido a "No se encontró …".

## Iteración 2

| Evidencia | Proceso | Requerimiento | Entidad | Módulo | Prueba(s) | Estado |
|---|---|---|---|---|---|---|
| E13, E14 | SLA de primer contacto y casos | RF-34 | Task.due_at | `services/business_time.py`, `crm.create_lead/create_case` | `test_iteracion2::test_add_business_hours` (7 casos: cierre, fin de semana, feriado, antes de abrir), `::test_business_hours_between_and_holidays`, `::test_first_contact_task_due_in_business_hours` | ✅ (feriados propios PENDIENTES) |
| E17, E19 | Deduplicación → fusión | RF-35 | Lead.merged_into_id, Activity, Task, Case, EmailClassification | `crm.merge_leads`, `POST /leads/{id}/merge`, `/api/leads/{id}/merge` | `::test_merge_leads_moves_history_and_keeps_trace`, `::test_merge_rejections` (3), `::test_merge_via_ui_and_api` | ✅ |
| E14 | Cotización enviada / PDF | RF-36 | Quote.sent_at, Task | `crm.change_quote_status`, `services/quote_pdf.py` | `::test_quote_status_flow`, `::test_quote_pdf`, `::test_quote_status_via_api_respects_rbac` | ✅ (envío manual por diseño, D-23) |
| E11 | Recompra | RF-38 | OrderReference, Task | `services/automations.py` | `::test_reorder_candidates_and_idempotent_tasks`, `::test_reorder_api` | ✅ lógica · 🟡 pedidos del ERP simulado · ⬜ programador diario |
| E17 | Clasificador medido de forma independiente | RF-40 (parcial) | — | `scripts/eval_corpus.py`, `data/eval/*` | Evaluación en 3 corpus (`05_EVALUACION_CLASIFICADOR.md`); `test_classifier::test_mixed_email_priority_rules` (6), `::test_company_suffix_sa_de_cv_is_not_a_job_application` | ✅ con datos sintéticos · ⬜ con correos reales |
| — | Seguridad de formularios y API | RNF-01 | — | `main.csrf_protect`, middleware | `::test_csrf_required_on_ui_forms`, `::test_login_form_requires_csrf`, `::test_api_rejects_non_json_bodies` | ✅ |
| — | Fuerza bruta en login | RNF-01 | — | `main.login` | `::test_login_rate_limit` | ✅ (en memoria, un proceso) |
| — | Migraciones versionadas | RNF-08 | todas | `migrations/` (Alembic 0001, 0002) | `::test_alembic_head_matches_models` (sin desfase + downgrade) | ✅ |
| E13 | Hora local en la interfaz | RNF-07 | — | filtro Jinja `local` | revisión visual (capturas) | ✅ |

### Hallazgos de verificación — iteración 2

1. **La cifra del clasificador de la iteración 1 era optimista**: con un corpus independiente, v1.0 acertaba 53 % (no 89 %). Documentado y corregido en v1.1.
2. **"S.A. de C.V." se leía como currículum** (regla de empleo) y arrastraba correos de pedido a OTRO. Corregido en rules-1.1.1, con prueba de regresión.
3. Las acciones de la API sin cuerpo (p. ej. `POST /api/integrations/erp-sync`) respondían 415 tras exigir JSON. Se ajustó: se rechaza cualquier Content-Type distinto de JSON y se permiten POST sin cuerpo.

## Iteración 3 — Historial total para administradores

Origen: requisito de Erii (21-sep-2026): "cada acción realizada por todos los usuarios de todas las áreas y tareas debe dejar registro e historial visible por el administrador principal o principales".

| Requisito | Módulo | Prueba(s) | Estado |
|---|---|---|---|
| Toda solicitud de todo usuario queda registrada (consulta, envío, descarga, exportación) con usuario, área, IP, ruta y resultado | middleware `_log_access` | `test_bitacora::test_every_request_of_every_user_is_logged` | ✅ |
| Todo cambio de datos tiene autor y área, incluidos los cambios automáticos | `audit.record` en servicios | `::test_all_business_events_have_an_actor`, `::test_business_events_freeze_actor_role_even_if_role_changes_later` | ✅ |
| Inicios y cierres de sesión, fallos y bloqueos | `main.login/logout` | `::test_auth_events_login_fail_lock_logout` | ✅ |
| Intentos rechazados (sin sesión, sin permiso, sin CSRF) | middleware | `::test_denied_attempts_are_logged_with_and_without_session` | ✅ |
| Nadie puede editar ni borrar el historial sin que se detecte | `audit.verify_chain`, listeners ORM | `::test_chain_detects_edit_and_delete`, `::test_orm_cannot_update_or_delete_audit` | ✅ |
| Visible solo para administradores, con filtros por usuario, área, tipo, entidad, acción y fechas; exportable a CSV | `/audit`, `/audit.csv`, `/api/audit`, `/api/audit/verify` | `::test_audit_views_admin_only_with_filters_and_csv` | ✅ |
| Historial dentro de cada registro (lead, cuenta, oportunidad, caso, correo) | `_history.html` | `::test_entity_history_visible_only_to_admin` | ✅ |
| Varios administradores; alta, baja, cambio de área y contraseña, todo registrado | `/admin/users`, `services/users.py` | `::test_user_management_is_audited_and_protected`, `::test_last_admin_and_self_protection` | ✅ |
| Migración de bases existentes sin perder historial | `migrations/0003` (encadena eventos previos) | `::test_migration_backfills_chain_for_existing_events` | ✅ |

Hallazgo de verificación: `verify_chain` leía objetos en caché de la sesión y **no detectaba** una alteración hecha por SQL en la misma sesión. Corregido con `populate_existing`; lo cubre `test_chain_detects_edit_and_delete`.
