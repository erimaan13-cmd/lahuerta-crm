"""Pipeline comercial, cotizaciones y subflujo de fórmula (RF-05, RF-06, RF-19)."""
import pytest
from sqlalchemy import select

from app.models import IntegrationEvent, Task
from app.services import crm
from app.services.common import DomainError, NotFound

ITEM = {"product_id": "ESP-001", "qty_kg": 600, "packaging": "saco_kraft_pe", "unit_price_mxn": 95}


@pytest.fixture()
def acc(db):
    return crm.create_account(db, {"name": "Cliente Prueba", "domain": "cp.example"}, None)


def _opp(db, acc, t="estandar"):
    return crm.create_opportunity(db, {"account_id": acc.id, "title": "Opp", "type": t, "est_volume_kg": 600,
                                       "product_ids": ["ESP-001"]}, "u-ventas")


def test_create_opportunity_validations(db, acc):
    with pytest.raises(NotFound):
        crm.create_opportunity(db, {"account_id": "nope", "title": "x"}, None)
    with pytest.raises(DomainError, match="Tipo"):
        crm.create_opportunity(db, {"account_id": acc.id, "title": "x", "type": "raro"}, None)
    with pytest.raises(DomainError, match="título"):
        crm.create_opportunity(db, {"account_id": acc.id, "title": " "}, None)


def test_invalid_transition_rejected(db, acc):
    o = _opp(db, acc)
    with pytest.raises(DomainError, match="no permitida"):
        crm.change_stage(db, o.id, "negociacion", None)
    with pytest.raises(DomainError, match="no permitida"):
        crm.change_stage(db, o.id, "desarrollo_formula", None)  # no aplica a estándar


def test_quotation_stage_requires_quote(db, acc):
    o = _opp(db, acc)
    with pytest.raises(DomainError, match="cotización"):
        crm.change_stage(db, o.id, "cotizacion", None)
    q = crm.create_quote(db, o.id, [ITEM], None)
    assert q.folio.startswith("COT-") and q.total_mxn == 57000 and q.total_kg == 600
    assert crm.change_stage(db, o.id, "cotizacion", None).stage == "cotizacion"
    assert o.est_value_mxn == 57000


@pytest.mark.parametrize("patch,msg", [
    ({"qty_kg": 0}, "mayor que cero"), ({"unit_price_mxn": -1}, "negativo"),
    ({"packaging": "bolsa"}, "Empaque"), ({"product_id": "X"}, "Producto"),
])
def test_quote_item_validation(db, acc, patch, msg):
    o = _opp(db, acc)
    with pytest.raises(DomainError, match=msg):
        crm.create_quote(db, o.id, [{**ITEM, **patch}], None)


def test_empty_quote_rejected(db, acc):
    with pytest.raises(DomainError, match="partida"):
        crm.create_quote(db, _opp(db, acc).id, [], None)


def test_lost_requires_reason_and_closes(db, acc):
    o = _opp(db, acc)
    with pytest.raises(DomainError, match="motivo"):
        crm.change_stage(db, o.id, "perdida", None, "  ")
    crm.change_stage(db, o.id, "perdida", None, "Precio")
    assert o.closed_at and o.lost_reason == "Precio"
    with pytest.raises(DomainError, match="cerrada"):
        crm.change_stage(db, o.id, "cotizacion", None)
    with pytest.raises(DomainError, match="cerrada"):
        crm.create_quote(db, o.id, [ITEM], None)


def test_won_updates_account_emits_integration_event_and_admin_task(db, acc):
    o = _opp(db, acc)
    crm.create_quote(db, o.id, [ITEM], None)
    crm.change_stage(db, o.id, "cotizacion", None)
    crm.change_stage(db, o.id, "ganada", "u-ventas")
    assert acc.lifecycle == "cliente_activo" and o.quotes[0].status == "aceptada"
    ev = db.scalar(select(IntegrationEvent).where(IntegrationEvent.event_type == "opportunity.won"))
    assert ev.system == "erp" and ev.payload["opportunity_id"] == o.id and ev.status == "pendiente"
    assert db.scalar(select(Task).where(Task.related_id == o.id, Task.assignee_role == "administracion"))


def test_formula_subflow_with_iteration(db, acc):
    o = _opp(db, acc, "formula_personalizada")
    with pytest.raises(DomainError):
        crm.change_stage(db, o.id, "cotizacion", None)  # debe pasar por desarrollo/muestra
    for s in ["desarrollo_formula", "muestra_enviada", "desarrollo_formula", "muestra_enviada", "muestra_aprobada"]:
        crm.change_stage(db, o.id, s, None)
    assert db.scalar(select(Task).where(Task.related_id == o.id, Task.assignee_role == "calidad"))
    crm.create_quote(db, o.id, [ITEM], None)
    crm.change_stage(db, o.id, "cotizacion", None)
    crm.change_stage(db, o.id, "negociacion", None)
    crm.change_stage(db, o.id, "ganada", None)
    assert o.stage == "ganada"


def test_stage_change_via_api(admin, db, acc):
    o = _opp(db, acc)
    r = admin.post(f"/api/opportunities/{o.id}/stage", json={"stage": "negociacion"})
    assert r.status_code == 422 and "no permitida" in r.json()["detail"]
    r = admin.post(f"/api/opportunities/{o.id}/quotes", json={"items": [ITEM]})
    assert r.status_code == 201 and r.json()["total_mxn"] == 57000
    assert admin.post(f"/api/opportunities/{o.id}/stage", json={"stage": "cotizacion"}).json()["stage"] == "cotizacion"
