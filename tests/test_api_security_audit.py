"""Autenticación, RBAC, auditoría, observabilidad, dashboard, integración ERP y end-to-end por API (RF-17, RF-20..22)."""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import config
from app.integrations.erp import ErpOrder, MockErpAdapter, sync_orders
from app.main import app
from app.models import Account, AuditEvent, IntegrationEvent, OrderReference
from app.security import make_session_token, read_session_token
from app.services import crm
from tests.conftest import ui_post

LEAD = {"full_name": "API Lead", "company_name": "API SA", "email": "api@apisa.example", "source": "web_contacto",
        "sector_code": "industria_alimentaria", "est_volume_kg": 2000, "product_interest_text": "comino"}


def test_unauthenticated(db):
    c = TestClient(app)
    assert c.get("/api/leads").status_code == 401
    r = c.get("/leads", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_bad_password_and_tampered_cookie(db):
    c = TestClient(app)
    assert ui_post(c, "/login", {"email": "admin@t.local", "password": "x"}).status_code == 401
    token = make_session_token("u-admin")
    assert read_session_token(token) == "u-admin"
    assert read_session_token(token[:-1] + ("0" if token[-1] != "0" else "1")) is None
    assert read_session_token("basura") is None
    c.cookies.set(config.SESSION_COOKIE, token[:-2] + "zz")
    assert c.get("/api/leads").status_code == 401


@pytest.mark.parametrize("role,method,path,body,expected", [
    ("lectura", "post", "/api/leads", LEAD, 403),
    ("calidad", "post", "/api/leads", LEAD, 403),
    ("atencion", "post", "/api/leads", LEAD, 201),
    ("ventas", "get", "/api/audit", None, 403),
    ("admin", "get", "/api/audit", None, 200),
    ("ventas", "get", "/api/export", None, 403),
    ("lectura", "get", "/api/dashboard", None, 200),
    ("calidad", "post", "/api/integrations/erp-sync", None, 403),
])
def test_rbac_matrix(client_for, role, method, path, body, expected):
    c = client_for(role)
    r = getattr(c, method)(path, json=body) if body is not None else getattr(c, method)(path)
    assert r.status_code == expected, r.text


def test_convert_permission(client_for, db):
    lead, _ = crm.create_lead(db, dict(LEAD), None)
    crm.change_lead_status(db, lead.id, "calificado", None)
    assert client_for("atencion").post(f"/api/leads/{lead.id}/convert", json={}).status_code == 403
    assert client_for("ventas").post(f"/api/leads/{lead.id}/convert", json={}).status_code == 200


def test_end_to_end_vertical_slice_1_via_api(client_for, db):
    """Formulario → lead → calificación → cuenta/contacto → oportunidad → cotización → etapa → actividad → tarea."""
    c = client_for("ventas")
    r = c.post("/api/leads", json=LEAD)
    assert r.status_code == 201
    lead_id = r.json()["lead"]["id"]
    assert c.post("/api/leads", json=LEAD).json()["created"] is False  # dedup
    assert c.post(f"/api/leads/{lead_id}/status", json={"status": "calificado"}).status_code == 200
    conv = c.post(f"/api/leads/{lead_id}/convert", json={"opp_type": "estandar"}).json()
    opp_id, acc_id = conv["opportunity"]["id"], conv["account"]["id"]
    q = c.post(f"/api/opportunities/{opp_id}/quotes", json={"items": [
        {"product_id": "ESP-001", "qty_kg": 2000, "packaging": "saco_kraft_pe", "unit_price_mxn": 92.5}]})
    assert q.status_code == 201 and q.json()["total_mxn"] == 185000
    assert c.post(f"/api/opportunities/{opp_id}/stage", json={"stage": "cotizacion"}).status_code == 200
    assert c.post("/api/activities", json={"type": "llamada", "subject": "Envié cotización", "related_type": "opportunity",
                                           "related_id": opp_id}).status_code == 201
    assert c.post("/api/tasks", json={"title": "Seguimiento cotización", "assignee_role": "ventas",
                                      "related_type": "opportunity", "related_id": opp_id}).status_code == 201
    acc = c.get(f"/api/accounts/{acc_id}").json()
    assert acc["opportunities"][0]["stage"] == "cotizacion" and acc["contacts"][0]["email"] == LEAD["email"]
    assert any(t["title"] == "Seguimiento cotización" for t in c.get("/api/tasks?role=ventas").json())
    assert c.get("/api/search?q=apisa").json()["accounts"][0]["id"] == acc_id
    m = c.get("/api/dashboard").json()
    assert m["pipeline"]["cotizacion"]["count"] == 1 and m["leads_by_status"]["convertido"] == 1


def test_audit_trail_records_actor_and_diff(client_for, db):
    c = client_for("ventas")
    lead_id = c.post("/api/leads", json=LEAD).json()["lead"]["id"]
    c.post(f"/api/leads/{lead_id}/status", json={"status": "calificado"}, headers={"X-Request-ID": "req-test-1"})
    events = client_for("admin").get(f"/api/audit?entity_id={lead_id}").json()
    actions = [e["action"] for e in events]
    assert actions[:2] == ["lead.create", "lead.status"]
    st = events[1]
    assert st["actor_id"] == "u-ventas" and st["before"]["status"] == "nuevo" and st["after"]["status"] == "calificado"
    assert st["request_id"] == "req-test-1"
    assert "password_hash" not in str(events)


def test_audit_is_append_only_no_mutation_routes():
    mutating = [r for r in app.routes if "audit" in getattr(r, "path", "") and set(getattr(r, "methods", [])) - {"GET", "HEAD"}]
    assert mutating == []


def test_errors_are_json_with_proper_codes(admin):
    assert admin.post("/api/leads", json={"full_name": ""}).status_code == 422
    assert admin.post("/api/leads/no-existe/status", json={"status": "contactado"}).status_code == 404
    assert admin.post("/api/opportunities/no-existe/stage", json={"stage": "cotizacion"}).json()["detail"].startswith("No se encontró Oportunidad")


def test_ui_domain_error_renders_page(admin):
    r = ui_post(admin, "/leads", {"full_name": "Sin contacto"})
    assert r.status_code == 422 and "Se requiere correo o teléfono" in r.text


def test_health_and_request_id(db):
    r = TestClient(app).get("/health", headers={"X-Request-ID": "abc"})
    assert r.json()["status"] == "ok" and r.headers["X-Request-ID"] == "abc"


def test_ui_pages_render_for_each_role(client_for, db):
    for role in ["admin", "ventas", "lectura"]:
        c = client_for(role)
        for p in ["/", "/leads", "/accounts", "/opportunities", "/tasks", "/cases", "/emails", "/emails/needs-review", "/search?q=ab"]:
            assert c.get(p).status_code == 200, (role, p)


def test_erp_sync_idempotent_lifecycle_and_unmatched(db):
    acc = crm.create_account(db, {"name": "ERP Cliente"}, None)
    acc.erp_customer_ref = "C-1"
    db.commit()
    orders = [ErpOrder("P-1", "C-1", "entregado", datetime(2026, 9, 1), datetime(2026, 9, 2), 600),
              ErpOrder("P-2", "C-1", "enviado", datetime(2026, 9, 20), None, 700),
              ErpOrder("P-3", "C-404", "recibido", None, None, 500)]
    assert sync_orders(db, MockErpAdapter(orders)) == {"created": 2, "updated": 0, "skipped": 1}
    assert sync_orders(db, MockErpAdapter(orders)) == {"created": 0, "updated": 2, "skipped": 1}
    assert len(db.scalars(select(OrderReference)).all()) == 2
    assert db.get(Account, acc.id).lifecycle == "cliente_recurrente"
    assert db.scalar(select(IntegrationEvent).where(IntegrationEvent.event_type == "order.unmatched_customer")).status == "error"
    assert db.scalar(select(AuditEvent).where(AuditEvent.action == "integration.erp_sync"))
