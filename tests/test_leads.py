"""Vertical slice 1 — captura, deduplicación, calificación y conversión de leads (RF-01..04, RF-08)."""
import pytest
from sqlalchemy import select

from app.models import Account, Activity, Contact, Lead, Opportunity, ProductInterest, Task
from app.services import crm
from app.services.common import DomainError

BASE = {"full_name": "Ana Prueba", "company_name": "Restaurante Uno", "email": "ana@uno.example",
        "phone": "81 1111 2222", "city": "Monterrey", "sector_code": "restaurante",
        "product_interest_text": "comino y pimienta", "est_volume_kg": 800, "source": "web_contacto"}


def test_create_lead_with_form_fields_and_first_contact_task(db):
    lead, created = crm.create_lead(db, dict(BASE), "u-ventas")
    assert created and lead.status == "nuevo" and lead.volume_band == "500kg_1t"
    assert lead.phone == "8111112222" and lead.below_minimum is False
    task = db.scalar(select(Task).where(Task.related_id == lead.id))
    assert task.origin == "auto_lead" and task.assignee_role == "ventas" and task.due_at is not None


@pytest.mark.parametrize("patch,msg", [
    ({"full_name": "  "}, "nombre"),
    ({"email": None, "phone": None}, "correo o teléfono"),
    ({"email": "no-es-correo"}, "Correo inválido"),
    ({"phone": "123"}, "Teléfono inválido"),
    ({"source": "tiktok"}, "Origen inválido"),
    ({"sector_code": "mineria"}, "Sector desconocido"),
    ({"est_volume_kg": -5}, "mayor que cero"),
    ({"volume_band": "gigante"}, "Rango de volumen"),
])
def test_create_lead_validation_errors(db, patch, msg):
    with pytest.raises(DomainError, match=msg):
        crm.create_lead(db, {**BASE, **patch}, None)


def test_below_minimum_flag(db):
    lead, _ = crm.create_lead(db, {**BASE, "email": "b@b.example", "est_volume_kg": 120}, None)
    assert lead.below_minimum and lead.volume_band == "menor_500kg"


def test_dedup_exact_email_does_not_create_new_lead(db):
    first, _ = crm.create_lead(db, dict(BASE), None)
    again, created = crm.create_lead(db, {**BASE, "email": "ANA@uno.example ", "message": "segunda vez"}, None)
    assert created is False and again.id == first.id
    assert db.scalar(select(Lead).where(Lead.email == "ana@uno.example").limit(2)) is not None
    assert len(db.scalars(select(Lead)).all()) == 1
    acts = db.scalars(select(Activity).where(Activity.related_id == first.id)).all()
    assert any("deduplicado" in a.subject for a in acts)


def test_possible_duplicate_by_phone_and_domain(db):
    a, _ = crm.create_lead(db, dict(BASE), None)
    b, _ = crm.create_lead(db, {**BASE, "email": None, "full_name": "Otro", "phone": "+52 81 1111 2222"}, None)
    assert b.possible_duplicate_of_id == a.id and b.duplicate_reason == "mismo teléfono"
    c, _ = crm.create_lead(db, {**BASE, "email": "compras@uno.example", "phone": None, "full_name": "Tercero"}, None)
    assert c.possible_duplicate_of_id == a.id and c.duplicate_reason == "mismo dominio"


def test_public_domain_is_not_duplicate_signal(db):
    crm.create_lead(db, {**BASE, "email": "x@gmail.com", "phone": None}, None)
    b, _ = crm.create_lead(db, {**BASE, "email": "y@gmail.com", "phone": None, "full_name": "Y"}, None)
    assert b.possible_duplicate_of_id is None


def test_status_transitions(db):
    lead, _ = crm.create_lead(db, dict(BASE), None)
    with pytest.raises(DomainError, match="motivo"):
        crm.change_lead_status(db, lead.id, "descartado", None, "")
    with pytest.raises(DomainError, match="no permitida"):
        crm.change_lead_status(db, lead.id, "convertido", None)
    crm.change_lead_status(db, lead.id, "contactado", None)
    crm.change_lead_status(db, lead.id, "calificado", None)
    assert lead.status == "calificado"


def test_qualify_requires_company(db):
    lead, _ = crm.create_lead(db, {**BASE, "company_name": None}, None)
    with pytest.raises(DomainError, match="empresa"):
        crm.change_lead_status(db, lead.id, "calificado", None)


def test_convert_requires_qualified(db):
    lead, _ = crm.create_lead(db, dict(BASE), None)
    with pytest.raises(DomainError, match="calificados"):
        crm.convert_lead(db, lead.id, None)


def test_convert_creates_account_contact_opportunity_with_products(db):
    lead, _ = crm.create_lead(db, dict(BASE), None)
    crm.change_lead_status(db, lead.id, "calificado", None)
    r = crm.convert_lead(db, lead.id, "u-ventas")
    assert r["account_created"] and r["account"].domain == "uno.example"
    assert r["contact"].email == "ana@uno.example" and r["contact"].account_id == r["account"].id
    opp = r["opportunity"]
    assert opp.stage == "requerimiento" and opp.est_volume_kg == 800
    skus = {pi.product_id for pi in db.scalars(select(ProductInterest).where(ProductInterest.opportunity_id == opp.id))}
    assert skus == {"ESP-001", "ESP-002"}
    assert lead.status == "convertido" and lead.converted_opportunity_id == opp.id


def test_convert_reuses_account_by_domain(db):
    acc = crm.create_account(db, {"name": "Uno SA", "domain": "uno.example"}, None)
    lead, _ = crm.create_lead(db, dict(BASE), None)
    crm.change_lead_status(db, lead.id, "calificado", None)
    r = crm.convert_lead(db, lead.id, None, create_opportunity=False)
    assert r["account"].id == acc.id and not r["account_created"] and r["opportunity"] is None
    assert len(db.scalars(select(Account)).all()) == 1


def test_convert_public_domain_does_not_set_account_domain(db):
    lead, _ = crm.create_lead(db, {**BASE, "email": "ana@gmail.com"}, None)
    crm.change_lead_status(db, lead.id, "calificado", None)
    r = crm.convert_lead(db, lead.id, None)
    assert r["account"].domain is None


def test_convert_twice_fails(db):
    lead, _ = crm.create_lead(db, dict(BASE), None)
    crm.change_lead_status(db, lead.id, "calificado", None)
    crm.convert_lead(db, lead.id, None)
    with pytest.raises(DomainError):
        crm.convert_lead(db, lead.id, None)
    assert len(db.scalars(select(Contact)).all()) == 1 and len(db.scalars(select(Opportunity)).all()) == 1


def test_duplicate_account_domain_rejected(db):
    crm.create_account(db, {"name": "A", "domain": "a.example"}, None)
    with pytest.raises(DomainError, match="dominio"):
        crm.create_account(db, {"name": "B", "domain": "A.example"}, None)
