"""Iteración 2: SLA hábil, fusión de duplicados, estado y PDF de cotización, recompra, CSRF, límite de login
y migraciones (RF-34..38, RNF-01, RNF-08)."""
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select

from app.db import Base
from app.integrations.erp import ErpOrder, MockErpAdapter, sync_orders
from app.main import app
from app.models import Activity, Case, Lead, Task, utcnow
from app.services import crm, email_pipeline
from app.services.automations import reorder_candidates, run_reorder_check
from app.services.business_time import (add_business_hours, business_hours_between, holidays,
                                        is_business_day, to_local)
from app.services.common import DomainError
from tests.conftest import PW, csrf, ui_post

ROOT = Path(__file__).resolve().parent.parent


def utc(y, m, d, h, mi=0):  # hora local Monterrey (UTC-6) → UTC naive
    return datetime(y, m, d, h, mi) + timedelta(hours=6)


# ------------------------------------------------------------------ SLA hábil (RF-34)
@pytest.mark.parametrize("start_local,hours,expected_local", [
    ((2026, 9, 21, 10, 0), 4, (2026, 9, 21, 14, 0)),   # lunes dentro del horario
    ((2026, 9, 21, 16, 0), 4, (2026, 9, 22, 11, 0)),   # cruza el cierre de las 17:00
    ((2026, 9, 18, 20, 0), 4, (2026, 9, 21, 12, 0)),   # viernes noche → lunes
    ((2026, 9, 19, 11, 0), 1, (2026, 9, 21, 9, 0)),    # sábado → lunes 8:00 + 1 h
    ((2026, 9, 15, 16, 30), 1, (2026, 9, 17, 8, 30)),  # 16-sep feriado
    ((2026, 9, 21, 6, 0), 2, (2026, 9, 21, 10, 0)),    # antes de abrir
    ((2026, 9, 21, 10, 0), 27, (2026, 9, 24, 10, 0)),  # 3 días hábiles de 9 h
])
def test_add_business_hours(start_local, hours, expected_local):
    got = to_local(add_business_hours(utc(*start_local), hours))
    assert got.replace(tzinfo=None) == datetime(*expected_local)


def test_business_hours_between_and_holidays():
    assert business_hours_between(utc(2026, 9, 18, 14), utc(2026, 9, 21, 10)) == 5.0
    assert business_hours_between(utc(2026, 9, 21, 10), utc(2026, 9, 21, 9)) == 0.0
    h = holidays(2026)
    assert {date(2026, 2, 2), date(2026, 3, 16), date(2026, 9, 16), date(2026, 11, 16), date(2026, 12, 25)} <= h
    assert date(2030, 10, 1) in holidays(2030) and date(2026, 10, 1) not in h
    assert not is_business_day(date(2026, 9, 20)) and is_business_day(date(2026, 9, 21))
    with pytest.raises(ValueError):
        add_business_hours(utcnow(), -1)


def test_first_contact_task_due_in_business_hours(db):
    lead, _ = crm.create_lead(db, {"full_name": "SLA", "email": "sla@x.example", "source": "web_contacto"}, None)
    due = to_local(db.scalar(select(Task).where(Task.related_id == lead.id)).due_at)
    assert is_business_day(due.date()) and 8 <= due.hour <= 17


# ------------------------------------------------------------------ fusión (RF-35)
def _leads(db):
    a, _ = crm.create_lead(db, {"full_name": "Óscar", "company_name": "Comedor Norte", "phone": "8120000014",
                                "source": "whatsapp", "est_volume_kg": 1200}, None)
    b, _ = crm.create_lead(db, {"full_name": "Roberto", "phone": "+52 81 2000 0014", "email": "rob@comedornorte.example",
                                "city": "Escobedo", "source": "telefono"}, None)
    return a, b


def test_merge_leads_moves_history_and_keeps_trace(db):
    a, b = _leads(db)
    assert b.possible_duplicate_of_id == a.id
    crm.log_activity(db, {"type": "llamada", "subject": "Llamada a Roberto", "related_type": "lead", "related_id": b.id}, None)
    case = crm.create_case(db, {"type": "otro", "subject": "Duda", "lead_id": b.id}, None)
    msg, _ = email_pipeline.process_raw(db, email_pipeline.RawEmail(provider="t", message_id="<m1>",
                                        from_email="rob@comedornorte.example", subject="Hola", body="¿me llaman?"))
    assert msg.classification.crm_link_id == b.id
    keep = crm.merge_leads(db, a.id, b.id, "u-ventas")
    assert keep.email == "rob@comedornorte.example" and keep.city == "Escobedo" and keep.company_name == "Comedor Norte"
    assert b.status == "descartado" and b.merged_into_id == a.id and "Fusionado" in b.discard_reason
    assert db.get(Case, case.id).lead_id == a.id
    assert msg.classification.crm_link_id == a.id and msg.classification.crm_links["lead"] == a.id
    assert any(x.subject == "Llamada a Roberto" for x in crm.timeline(db, "lead", a.id))
    assert db.scalars(select(Activity).where(Activity.related_id == b.id)).all() == []
    auto = db.scalars(select(Task).where(Task.related_id == b.id, Task.origin == "auto_lead")).all()
    assert all(t.status == "cancelada" for t in auto)


@pytest.mark.parametrize("case", ["self", "converted", "already"])
def test_merge_rejections(db, case):
    a, b = _leads(db)
    if case == "self":
        with pytest.raises(DomainError, match="consigo mismo"):
            crm.merge_leads(db, a.id, a.id, None)
    elif case == "converted":
        crm.change_lead_status(db, a.id, "calificado", None)
        crm.convert_lead(db, a.id, None, create_opportunity=False)
        with pytest.raises(DomainError, match="convertido"):
            crm.merge_leads(db, a.id, b.id, None)
    else:
        crm.merge_leads(db, a.id, b.id, None)
        with pytest.raises(DomainError, match="fusionado"):
            crm.merge_leads(db, a.id, b.id, None)


def test_merge_via_ui_and_api(client_for, db):
    a, b = _leads(db)
    c = client_for("ventas")
    assert c.post(f"/api/leads/{b.id}/merge", json={"keep_id": a.id}).json()["id"] == a.id
    a2, b2 = crm.create_lead(db, {"full_name": "X", "phone": "8130000000", "source": "otro"}, None)[0], \
        crm.create_lead(db, {"full_name": "Y", "phone": "8130000000", "source": "otro"}, None)[0]
    r = ui_post(c, f"/leads/{b2.id}/merge", {"keep_id": a2.id}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == f"/leads/{a2.id}"


# ------------------------------------------------------------------ cotización: estado y PDF (RF-36)
@pytest.fixture()
def quote(db):
    acc = crm.create_account(db, {"name": "Cliente PDF", "is_demo": True}, None)
    opp = crm.create_opportunity(db, {"account_id": acc.id, "title": "Opp PDF"}, None)
    return crm.create_quote(db, opp.id, [{"product_id": "ESP-001", "qty_kg": 600, "packaging": "saco_kraft_pe",
                                          "unit_price_mxn": 95}], None)


def test_quote_status_flow(db, quote):
    with pytest.raises(DomainError, match="no permitida"):
        crm.change_quote_status(db, quote.id, "aceptada", None)
    crm.change_quote_status(db, quote.id, "enviada", "u-ventas")
    assert quote.sent_at is not None
    assert db.scalar(select(Task).where(Task.origin == "auto_quote", Task.related_id == quote.opportunity_id))
    crm.change_quote_status(db, quote.id, "rechazada", None)
    with pytest.raises(DomainError):
        crm.change_quote_status(db, quote.id, "enviada", None)


def test_quote_pdf(client_for, quote):
    c = client_for("lectura")
    r = c.get(f"/quotes/{quote.id}.pdf")
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF") and quote.folio.encode() in r.content  # folio en el título del PDF
    assert c.get("/api/quotes/no-existe/pdf").status_code == 404
    assert client_for(None).get(f"/api/quotes/{quote.id}/pdf").status_code == 401


def test_quote_status_via_api_respects_rbac(client_for, quote):
    assert client_for("calidad").post(f"/api/quotes/{quote.id}/status", json={"status": "enviada"}).status_code == 403
    assert client_for("ventas").post(f"/api/quotes/{quote.id}/status", json={"status": "enviada"}).json()["status"] == "enviada"


# ------------------------------------------------------------------ recompra (RF-38)
def test_reorder_candidates_and_idempotent_tasks(db):
    now = datetime(2026, 9, 21, 12)
    late = crm.create_account(db, {"name": "Atrasado"}, None)
    ok = crm.create_account(db, {"name": "Al corriente"}, None)
    single = crm.create_account(db, {"name": "Un pedido"}, None)
    prospect = crm.create_account(db, {"name": "Prospecto sin pedidos"}, None)
    for a, ref in [(late, "C-L"), (ok, "C-O"), (single, "C-S")]:
        a.erp_customer_ref = ref
    db.commit()
    orders = [ErpOrder("1", "C-L", "entregado", None, now - timedelta(days=95), 1000),
              ErpOrder("2", "C-L", "entregado", None, now - timedelta(days=60), 1000),   # intervalo 35 d → atraso
              ErpOrder("3", "C-O", "entregado", None, now - timedelta(days=40), 1000),
              ErpOrder("4", "C-O", "entregado", None, now - timedelta(days=10), 1000),   # intervalo 30 d → al corriente
              ErpOrder("5", "C-S", "entregado", None, now - timedelta(days=45), 700)]    # 1 pedido, >36 d → atraso
    sync_orders(db, MockErpAdapter(orders))
    names = [c["account"].name for c in reorder_candidates(db, now)]
    assert names == ["Atrasado", "Un pedido"] and prospect.name not in names
    assert run_reorder_check(db, None, now) == {"created": 2, "skipped_existing": 0}
    assert run_reorder_check(db, None, now) == {"created": 0, "skipped_existing": 2}
    t = db.scalar(select(Task).where(Task.origin == "auto_recompra", Task.related_id == late.id))
    assert t.assignee_role == "ventas" and "Atrasado" in t.title


def test_reorder_api(client_for, db):
    assert client_for("ventas").post("/api/automations/reorder-check").status_code == 403
    assert client_for("admin").post("/api/automations/reorder-check").status_code == 200
    assert client_for("lectura").get("/api/automations/reorder-candidates").status_code == 200


# ------------------------------------------------------------------ seguridad (RNF-01)
def test_csrf_required_on_ui_forms(client_for, db):
    c = client_for("ventas")
    data = {"full_name": "CSRF", "email": "csrf@x.example", "source": "otro"}
    assert c.post("/leads", data=data).status_code == 403                                # sin token
    assert c.post("/leads", data={**data, "csrf_token": "falso"}).status_code == 403     # token incorrecto
    assert db.scalar(select(Lead).where(Lead.email == "csrf@x.example")) is None
    assert ui_post(c, "/leads", data, follow_redirects=False).status_code == 303


def test_login_form_requires_csrf(db):
    c = TestClient(app)
    assert c.post("/login", data={"email": "admin@t.local", "password": PW}).status_code == 403


def test_api_rejects_non_json_bodies(admin):
    r = admin.post("/api/leads", content=b'{"full_name":"x","email":"x@y.example"}', headers={"Content-Type": "text/plain"})
    assert r.status_code == 415


def test_login_rate_limit(db):
    c = TestClient(app)
    for _ in range(5):
        assert ui_post(c, "/login", {"email": "admin@t.local", "password": "mala"}).status_code == 401
    r = ui_post(c, "/login", {"email": "admin@t.local", "password": PW})
    assert r.status_code == 429 and "Demasiados intentos" in r.text
    other = ui_post(TestClient(app), "/login", {"email": "ventas@t.local", "password": PW}, follow_redirects=False)
    assert other.status_code == 303  # el bloqueo es por (ip, correo), no global


# ------------------------------------------------------------------ migraciones (RNF-08)
def test_alembic_head_matches_models(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    monkeypatch.setattr("app.config.DATABASE_URL", url)
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(cfg, "head")
    insp = inspect(create_engine(url))
    migrated = {t: {c["name"] for c in insp.get_columns(t)} for t in insp.get_table_names() if t != "alembic_version"}
    expected = {t.name: {c.name for c in t.columns} for t in Base.metadata.sorted_tables}
    assert migrated == expected
    command.downgrade(cfg, "0001")
    assert "merged_into_id" not in {c["name"] for c in inspect(create_engine(url)).get_columns("leads")}
