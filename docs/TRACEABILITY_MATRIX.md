# TRACEABILITY_MATRIX

`EVIDENCIA → PROCESO → REQUERIMIENTO → ENTIDAD → MÓDULO → PRUEBA`
Evidencias: `docs/01_INVESTIGACION.md §2`. Requerimientos: `docs/02_PLAN.md §1`. Pruebas en `tests/` (95 casos, **todos pasan** — ejecución del 21-sep-2026). Estado: ✅ implementado y probado · 🟡 simulado/mock probado · ⬜ solo diseño.

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
| E14 | Seguimiento / SLA | RF-08 | Task | `crm.create_lead` (auto), `crm.create_task/complete_task` | `test_leads::test_create_lead_with_form_fields_and_first_contact_task`, `test_activities_cases_search::test_task_lifecycle` | ✅ (SLA en horas naturales, no hábiles) |
| — | Búsqueda y filtros | RF-09 | Lead, Account, Contact, Opportunity | `crm.search`, `crm.filter_leads` | `test_activities_cases_search::test_search_by_name_company_email_phone_and_short_query`, `::test_filters` | ✅ |
| E17 | Ingesta de correo | RF-10 | EmailMessage | `integrations/email_providers.py`, `email_pipeline.ingest` | `test_email_pipeline::test_ingest_is_idempotent_and_counts_errors`, `::test_eml_parsing_html_attachment_and_directory`, `::test_gmail_provider_is_explicitly_not_implemented` | ✅ EML/mock · ⬜ Gmail |
| — | Normalización | RF-11 | EmailMessage.body_clean | `classifier/normalize.py` | `test_classifier::test_normalization_strips_html_and_quoted_history` | ✅ |
| E17, E03, E06, E08 | Clasificación con confianza | RF-12 | EmailClassification | `classifier/rules.py`, `engine.py` | `test_classifier::test_categories` (11 categorías), `::test_known_sender_is_never_new_lead`, `::test_hybrid_llm_only_called_when_uncertain`, `::test_llm_disabled_by_default` | ✅ reglas · 🟡 LLM (mock) |
| E09–E11 | Extracción de entidades | RF-13 | EmailClassification.extracted_entities | `classifier/extract.py` | `test_classifier::test_extraction_fields`, `::test_extraction_edge_cases` | ✅ |
| — | Vinculación CRM | RF-14 | EmailClassification.crm_link* | `email_pipeline.resolve_sender/link_references` | `test_email_pipeline::test_link_to_contact_and_opportunity_by_quote_folio`, `::test_link_by_corporate_domain_when_sender_unknown` | ✅ |
| — | Enrutamiento y sugerencia | RF-15 | EmailClassification.suggested_* | `classifier/taxonomy.py`, `email_pipeline.apply_suggestion` | `test_classifier::test_new_sender_quote_suggests_create_lead_known_sender_suggests_task`, `test_email_pipeline::test_review_then_apply_create_lead`, `::test_apply_task_for_order_email`, `::test_supplier_email_routed_outside_crm`, `::test_open_case_without_link_fails` | ✅ |
| E24 | Revisión humana | RF-16 | EmailClassification.review_status | `email_pipeline.review`, `/emails/needs-review` | `test_classifier::test_no_signal_goes_to_needs_review_as_other`, `::test_quality_claim_always_needs_review_even_with_high_confidence`, `::test_ambiguous_mixed_email_needs_review_by_margin`, `::test_english_email_is_not_forced_into_a_category`, `test_email_pipeline::test_review_invalid_category` | ✅ |
| — | Contrato de salida del clasificador | RF-12..15 | — | `GET /api/emails` | `test_email_pipeline::test_api_email_contract` | ✅ |
| — | Dashboard | RF-17 | (agregados) | `services/dashboard.py`, `/` | `test_api_security_audit::test_end_to_end_vertical_slice_1_via_api` (métricas), `::test_ui_pages_render_for_each_role` | ✅ |
| E03, E24 | Reclamación / caso | RF-18 | Case, IntegrationEvent | `crm.create_case/change_case_status` | `test_activities_cases_search::test_quality_claim_requires_lot_to_resolve_and_escalates_to_qms`, `::test_case_invalid_type_and_severity`, `test_email_pipeline::test_quality_claim_opens_case_with_lot_after_human_confirmation` | ✅ · 🟡 QMS (evento) |
| E10, E14 | Cotización | RF-19 | Quote, QuoteItem | `crm.create_quote` | `test_pipeline::test_quotation_stage_requires_quote`, `::test_quote_item_validation`, `::test_empty_quote_rejected` | ✅ (sin PDF) |
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
