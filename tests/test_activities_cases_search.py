"""Interacciones, tareas, casos, búsqueda y filtros (RF-07, RF-08, RF-09, RF-18)."""
import pytest
from sqlalchemy import select

from app.models import IntegrationEvent, Task
from app.services import crm
from app.services.common import DomainError, NotFound

LEAD = {"full_name": "Beto Búsqueda", "company_name": "Taquería Norte", "email": "beto@tnorte.example",
        "phone": "8122223333", "sector_code": "restaurante", "source": "whatsapp"}


def test_activity_on_new_lead_marks_contacted_and_closes_first_contact_task(db):
    lead, _ = crm.create_lead(db, dict(LEAD), None)
    crm.log_activity(db, {"type": "llamada", "subject": "Llamada inicial", "related_type": "lead", "related_id": lead.id}, "u-ventas")
    assert lead.status == "contactado"
    t = db.scalar(select(Task).where(Task.related_id == lead.id, Task.origin == "auto_lead"))
    assert t.status == "hecha"
    assert crm.timeline(db, "lead", lead.id)[0].subject == "Llamada inicial"


@pytest.mark.parametrize("data,err", [
    ({"type": "llamada", "subject": "x", "related_type": "planeta", "related_id": "1"}, DomainError),
    ({"type": "llamada", "subject": "x", "related_type": "lead", "related_id": "no-existe"}, NotFound),
    ({"type": "sistema", "subject": "x", "related_type": "lead", "related_id": None}, DomainError),
])
def test_activity_validation(db, data, err):
    if data["related_id"] is None:
        data["related_id"] = crm.create_lead(db, dict(LEAD), None)[0].id
    with pytest.raises(err):
        crm.log_activity(db, data, None)


def test_task_lifecycle(db):
    t = crm.create_task(db, {"title": "Llamar", "assignee_role": "ventas", "due_at": "2026-09-22T10:00"}, None)
    crm.complete_task(db, t.id, None)
    with pytest.raises(DomainError, match="no está pendiente"):
        crm.complete_task(db, t.id, None)
    with pytest.raises(DomainError):
        crm.create_task(db, {"title": ""}, None)


def test_search_by_name_company_email_phone_and_short_query(db):
    lead, _ = crm.create_lead(db, dict(LEAD), None)
    for q in ["beto", "TAQUERÍA".lower(), "tnorte.example", "2222 3333"]:
        assert lead.id in [x.id for x in crm.search(db, q)["leads"]], q
    assert crm.search(db, "b") == {"leads": [], "accounts": [], "contacts": [], "opportunities": []}


def test_filters(db):
    crm.create_lead(db, dict(LEAD), None)
    crm.create_lead(db, {**LEAD, "email": "h@hotel.example", "phone": None, "sector_code": "hotel", "source": "google_ads",
                         "est_volume_kg": 100}, None)
    assert len(crm.filter_leads(db, sector="hotel")) == 1
    assert len(crm.filter_leads(db, source="whatsapp")) == 1
    assert len(crm.filter_leads(db, below_minimum=True)) == 1
    assert len(crm.filter_leads(db, status="nuevo")) == 2


def test_quality_claim_requires_lot_to_resolve_and_escalates_to_qms(db):
    acc = crm.create_account(db, {"name": "Comedor X"}, None)
    with pytest.raises(DomainError, match="cuenta o a un lead"):
        crm.create_case(db, {"type": "reclamacion_calidad", "subject": "x"}, None)
    c = crm.create_case(db, {"type": "reclamacion_calidad", "severity": "alta", "subject": "Humedad", "account_id": acc.id}, None)
    assert c.folio.startswith("CASO-")
    assert db.scalar(select(Task).where(Task.related_id == c.id)).assignee_role == "calidad"
    crm.change_case_status(db, c.id, "escalado_qms", None)
    assert db.scalar(select(IntegrationEvent).where(IntegrationEvent.event_type == "case.escalated"))
    with pytest.raises(DomainError, match="lote"):
        crm.change_case_status(db, c.id, "resuelto", None)
    crm.change_case_status(db, c.id, "resuelto", None, lot_reference="L-1")
    crm.change_case_status(db, c.id, "cerrado", None)
    with pytest.raises(DomainError, match="no permitida"):
        crm.change_case_status(db, c.id, "abierto", None)


def test_case_invalid_type_and_severity(db):
    acc = crm.create_account(db, {"name": "Y"}, None)
    with pytest.raises(DomainError, match="Tipo"):
        crm.create_case(db, {"type": "queja", "subject": "s", "account_id": acc.id}, None)
    with pytest.raises(DomainError, match="Severidad"):
        crm.create_case(db, {"type": "otro", "severity": "extrema", "subject": "s", "account_id": acc.id}, None)
