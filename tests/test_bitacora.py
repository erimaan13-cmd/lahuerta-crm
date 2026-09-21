"""Iteración 3 — Historial total: toda acción de todo usuario queda registrada, encadenada y visible solo
para administradores."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text

from app.audit import verify_chain
from app.main import app
from app.models import AuditEvent, User, utcnow
from app.services.business_time import to_local
from app.services import crm
from app.services import users as users_svc
from app.services.common import DomainError
from tests.conftest import PW, ui_post

ROOT = Path(__file__).resolve().parent.parent
LEAD = {"full_name": "Bitácora", "company_name": "Log SA", "email": "log@logsa.example", "source": "web_contacto",
        "est_volume_kg": 800}


def events(db, **filters):
    db.expire_all()
    stmt = select(AuditEvent).order_by(AuditEvent.seq)
    for k, v in filters.items():
        stmt = stmt.where(getattr(AuditEvent, k) == v)
    return list(db.scalars(stmt))


# ------------------------------------------------------------------ cobertura: cada acción queda registrada
def test_every_request_of_every_user_is_logged(client_for, db):
    c = client_for("ventas")
    before = len(events(db, actor_id="u-ventas"))
    lead_id = c.post("/api/leads", json=LEAD).json()["lead"]["id"]           # operación API
    c.get("/leads")                                                            # consulta de lista
    c.get(f"/leads/{lead_id}")                                                 # consulta de un registro
    ui_post(c, f"/leads/{lead_id}/status", {"status": "contactado"}, follow_redirects=False)  # formulario
    c.get("/api/dashboard")                                                    # consulta API
    evs = events(db, actor_id="u-ventas")[before:]
    access = [e for e in evs if e.category == "acceso"]
    assert len(access) == 5
    assert all(e.actor_email == "ventas@t.local" and e.actor_role == "ventas" and e.ip for e in evs)
    view = next(e for e in access if e.method == "GET" and e.entity_type == "lead")
    assert view.entity_id == lead_id and view.status == 200 and view.action == "acceso.consulta"
    business = [e.action for e in evs if e.category == "negocio"]
    assert "lead.create" in business and "lead.status" in business


def test_business_events_freeze_actor_role_even_if_role_changes_later(client_for, db):
    c = client_for("atencion")
    c.post("/api/leads", json=LEAD)
    users_svc.change_role(db, "u-atencion", "ventas", "u-admin")
    ev = events(db, action="lead.create")[-1]
    assert ev.actor_role == "atencion"  # el historial no se reescribe


def test_auth_events_login_fail_lock_logout(db):
    c = TestClient(app)
    ui_post(c, "/login", {"email": "calidad@t.local", "password": "mala"})
    ui_post(c, "/login", {"email": "nadie@t.local", "password": "x"})
    ui_post(c, "/login", {"email": "calidad@t.local", "password": PW}, follow_redirects=False)
    ui_post(c, "/logout", follow_redirects=False)
    acts = [(e.action, (e.after or {}).get("motivo")) for e in events(db, category="seguridad")]
    assert ("auth.login_fallido", "contraseña incorrecta") in acts and ("auth.login_fallido", "usuario inexistente") in acts
    assert ("auth.login", None) in acts and ("auth.logout", None) in acts
    for _ in range(5):
        ui_post(c, "/login", {"email": "lectura@t.local", "password": "mala"})
    ui_post(c, "/login", {"email": "lectura@t.local", "password": PW})
    assert events(db, action="auth.bloqueado")


def test_denied_attempts_are_logged_with_and_without_session(client_for, db):
    TestClient(app).get("/api/leads")                                          # anónimo → 401
    client_for("ventas").get("/audit")                                         # sin permiso → 403
    client_for("ventas").post("/leads", data={"full_name": "x"})              # sin CSRF → 403
    denied = events(db, action="acceso.denegado")
    assert any(e.status == 401 and e.actor_id is None for e in denied)
    assert sum(1 for e in denied if e.status == 403 and e.actor_id == "u-ventas") == 2
    assert all(e.category == "seguridad" for e in denied)


def test_all_business_events_have_an_actor(client_for, db):
    c = client_for("ventas")
    lid = c.post("/api/leads", json=LEAD).json()["lead"]["id"]
    c.post("/api/activities", json={"type": "llamada", "subject": "hola", "related_type": "lead", "related_id": lid})
    c.post(f"/api/leads/{lid}/status", json={"status": "calificado"})
    opp = c.post(f"/api/leads/{lid}/convert", json={}).json()["opportunity"]["id"]
    c.post(f"/api/opportunities/{opp}/quotes", json={"items": [{"product_id": "ESP-001", "qty_kg": 600,
                                                              "packaging": "saco_pp_pead", "unit_price_mxn": 90}]})
    c.post(f"/api/opportunities/{opp}/stage", json={"stage": "cotizacion"})
    biz = events(db, category="negocio")
    assert len(biz) >= 8 and all(e.actor_id == "u-ventas" and e.actor_role == "ventas" for e in biz)
    auto = [e for e in biz if e.summary and "Automático" in e.summary]
    assert auto  # el cambio automático a "contactado" también queda registrado


# ------------------------------------------------------------------ integridad
def test_chain_detects_edit_and_delete(client_for, db):
    c = client_for("ventas")
    for i in range(3):
        c.post("/api/leads", json={**LEAD, "email": f"x{i}@logsa.example"})
    assert verify_chain(db)["ok"]
    target = events(db, action="lead.create")[1]
    db.execute(text("UPDATE audit_events SET summary='manipulado' WHERE id=:i"), {"i": target.id})
    db.commit()
    r = verify_chain(db)
    assert not r["ok"] and r["broken_seq"] == target.seq and r["reason"] == "contenido alterado"
    db.execute(text("UPDATE audit_events SET summary=:s WHERE id=:i"), {"s": None, "i": target.id})
    db.execute(text("DELETE FROM audit_events WHERE seq=2"))
    db.commit()
    r = verify_chain(db)
    assert not r["ok"] and r["broken_seq"] == 2 and "falta" in r["reason"]


def test_orm_cannot_update_or_delete_audit(db):
    crm.create_lead(db, dict(LEAD), "u-ventas")
    ev = events(db)[0]
    ev.summary = "cambio"
    with pytest.raises(PermissionError):
        db.commit()
    db.rollback()
    db.delete(events(db)[0])
    with pytest.raises(PermissionError):
        db.commit()
    db.rollback()


# ------------------------------------------------------------------ visibilidad solo para administradores
def test_audit_views_admin_only_with_filters_and_csv(client_for, db):
    v = client_for("ventas")
    lid = v.post("/api/leads", json=LEAD).json()["lead"]["id"]
    for role in ["ventas", "calidad", "lectura", "administracion", "atencion"]:
        assert client_for(role).get("/audit").status_code == 403
        assert client_for(role).get("/audit.csv").status_code == 403
    a = client_for("admin")
    page = a.get("/audit?actor=u-ventas")
    assert page.status_code == 200 and "Integridad verificada" in page.text and "ventas@t.local" in page.text
    assert "lead.create" in a.get("/audit?role=ventas&category=negocio").text
    today = to_local(utcnow()).strftime("%Y-%m-%d")  # fecha de Monterrey
    assert "lead.create" in a.get(f"/audit?desde={today}&hasta={today}&entity_id={lid}").text
    assert a.get("/audit?desde=ayer").status_code == 422
    csv_resp = a.get("/audit.csv?actor=u-ventas")
    body = csv_resp.content.decode("utf-8-sig")
    assert csv_resp.headers["content-type"].startswith("text/csv") and body.startswith("seq,fecha_local,usuario")
    assert "lead.create" in body and "ventas@t.local" in body
    assert a.get("/api/audit/verify").json()["ok"] is True
    assert len(a.get("/api/audit?actor=u-ventas&category=negocio").json()) >= 1


def test_entity_history_visible_only_to_admin(client_for, db):
    v = client_for("ventas")
    lid = v.post("/api/leads", json=LEAD).json()["lead"]["id"]
    assert "Historial de este registro" not in v.get(f"/leads/{lid}").text
    html = client_for("admin").get(f"/leads/{lid}").text
    assert "Historial de este registro" in html and "lead.create" in html and "ventas@t.local" in html


# ------------------------------------------------------------------ gestión de usuarios auditada
def test_user_management_is_audited_and_protected(client_for, db):
    a = client_for("admin")
    r = ui_post(a, "/admin/users", {"full_name": "Nuevo Admin", "email": "admin2@t.local", "role": "admin",
                                    "password": "segura-12345"}, follow_redirects=False)
    assert r.status_code == 303
    new = db.scalar(select(User).where(User.email == "admin2@t.local"))
    assert ui_post(TestClient(app), "/login", {"email": "admin2@t.local", "password": "segura-12345"},
                   follow_redirects=False).status_code == 303
    ui_post(a, f"/admin/users/{new.id}/password", {"password": "otra-clave-123"})
    ui_post(a, f"/admin/users/{new.id}/active", {"active": "0"})
    assert ui_post(TestClient(app), "/login", {"email": "admin2@t.local", "password": "otra-clave-123"}).status_code == 401
    acts = [e.action for e in events(db, entity_id=new.id, category="seguridad")]
    assert {"usuario.crear", "usuario.restablecer_contrasena", "usuario.desactivar"} <= set(acts)
    assert all("otra-clave" not in str(e.after) + str(e.summary) for e in events(db))
    assert client_for("ventas").get("/admin/users").status_code == 403


def test_last_admin_and_self_protection(db):
    with pytest.raises(DomainError, match="último administrador"):
        users_svc.set_active(db, "u-admin", False, "u-ventas")
    with pytest.raises(DomainError, match="último administrador"):
        users_svc.change_role(db, "u-admin", "ventas", "u-ventas")
    users_svc.create_user(db, {"full_name": "B", "email": "b@t.local", "role": "admin", "password": "x" * 12}, "u-admin")
    with pytest.raises(DomainError, match="propia cuenta"):
        users_svc.set_active(db, "u-admin", False, "u-admin")
    with pytest.raises(DomainError, match="al menos"):
        users_svc.create_user(db, {"full_name": "C", "email": "c@t.local", "role": "ventas", "password": "corta"}, "u-admin")


# ------------------------------------------------------------------ migración con datos previos
def test_migration_backfills_chain_for_existing_events(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    url = f"sqlite:///{tmp_path / 'old.db'}"
    monkeypatch.setattr("app.config.DATABASE_URL", url)
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(cfg, "0002")
    eng = create_engine(url)
    with eng.begin() as con:
        for i in range(3):
            con.execute(text("INSERT INTO audit_events (id, at, actor_id, action, entity_type, entity_id, before, after, "
                             "request_id) VALUES (:id, :at, 'u1', 'lead.create', 'lead', :e, NULL, :a, NULL)"),
                        {"id": f"old-{i}", "at": f"2026-09-2{i} 10:00:00.000000", "e": f"L{i}", "a": '{"x": 1}'})
    command.upgrade(cfg, "head")
    from sqlalchemy.orm import Session
    with Session(eng) as s:
        r = verify_chain(s)
        assert r == {"ok": True, "checked": 3, "broken_seq": None, "reason": None}
        assert [e.category for e in s.scalars(select(AuditEvent))] == ["negocio"] * 3
