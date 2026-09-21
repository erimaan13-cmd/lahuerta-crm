"""Vertical slice 2 — Email → ingesta → clasificación → extracción → vínculo CRM → sugerencia → revisión (RF-10..16)."""
from email.message import EmailMessage as PyEmail

import pytest
from sqlalchemy import select

from app.integrations.email_providers import EmlDirectoryProvider, GmailProvider, RawEmail, parse_eml_bytes
from app.models import Case, EmailMessage, Lead, Task
from app.services import crm, email_pipeline
from app.services.common import DomainError


class ListProvider:
    name = "test"

    def __init__(self, items):
        self.items = items

    def fetch(self):
        return self.items


def raw(mid, sender, subject, body):
    return RawEmail(provider="test", message_id=mid, from_email=sender, subject=subject, body=body)


@pytest.fixture()
def world(db):
    acc = crm.create_account(db, {"name": "Cliente Correo", "domain": "cc.example"}, None)
    contact = crm.create_contact(db, acc.id, {"full_name": "Compras CC", "email": "compras@cc.example"}, None)
    opp = crm.create_opportunity(db, {"account_id": acc.id, "title": "Opp CC"}, None)
    q = crm.create_quote(db, opp.id, [{"product_id": "ESP-001", "qty_kg": 500, "packaging": "saco_pp_pead", "unit_price_mxn": 90}], None)
    return {"acc": acc, "contact": contact, "opp": opp, "quote": q}


def test_ingest_is_idempotent_and_counts_errors(db):
    items = [raw("<a1>", "nuevo@rest.example", "Cotización", "cotizar 600 kg de comino"),
             raw("<a1>", "nuevo@rest.example", "Cotización", "duplicado"),
             raw("<bad>", "sin-arroba", "x", "y")]
    s = email_pipeline.ingest(db, ListProvider(items))
    assert (s["fetched"], s["new"], s["duplicates"], s["errors"]) == (3, 1, 1, 1)
    s2 = email_pipeline.ingest(db, ListProvider(items[:1]))
    assert s2["new"] == 0 and s2["duplicates"] == 1
    assert len(db.scalars(select(EmailMessage)).all()) == 1


def test_link_to_contact_and_opportunity_by_quote_folio(db, world):
    msg, _ = email_pipeline.process_raw(db, raw("<s1>", "compras@cc.example", f"RE: {world['quote'].folio}",
                                                f"Respecto a la cotización {world['quote'].folio}, ¿pueden mejorar el precio?"))
    c = msg.classification
    assert c.category == "SEGUIMIENTO_COMERCIAL" and c.crm_link_type == "opportunity" and c.crm_link_id == world["opp"].id
    assert c.crm_links["contact"] == world["contact"].id and c.extracted_entities["company"] == "Cliente Correo"
    assert crm.timeline(db, "opportunity", world["opp"].id)[0].type == "correo"


def test_link_by_corporate_domain_when_sender_unknown(db, world):
    msg, _ = email_pipeline.process_raw(db, raw("<d1>", "otra.persona@cc.example", "Factura", "Favor de enviar la factura XML"))
    assert msg.classification.extracted_entities["sender_kind"] == "cuenta_dominio"
    assert msg.classification.crm_link_type == "account"


def test_review_then_apply_create_lead(db):
    msg, _ = email_pipeline.process_raw(db, raw("<l1>", "chef@nuevohotel.example", "Hola",
                                                "Hola, trabajo en un hotel en Monterrey. ¿Me pueden llamar? Tel 81 5555 6666"))
    cls = msg.classification
    assert cls.review_status == "needs_review"
    with pytest.raises(DomainError, match="Needs Review"):
        email_pipeline.apply_suggestion(db, msg.id, "u-ventas")
    email_pipeline.review(db, msg.id, "u-ventas", "LEAD_NUEVO")
    assert cls.review_status == "corregido" and cls.final_category == "LEAD_NUEVO" and cls.suggested_action == "crear_lead"
    res = email_pipeline.apply_suggestion(db, msg.id, "u-ventas")
    lead = db.get(Lead, res["entity_id"])
    assert lead.source == "email" and lead.phone == "8155556666" and lead.city == "Monterrey" and lead.sector_code == "hotel"
    assert cls.review_status == "aplicado" and cls.crm_links["lead"] == lead.id
    with pytest.raises(DomainError, match="ya fue aplicada"):
        email_pipeline.apply_suggestion(db, msg.id, "u-ventas")
    with pytest.raises(DomainError, match="ya fue aplicada"):
        email_pipeline.review(db, msg.id, "u-ventas")


def test_review_invalid_category(db):
    msg, _ = email_pipeline.process_raw(db, raw("<r1>", "a@b.example", "Hola", "llámame"))
    with pytest.raises(DomainError, match="Categoría inválida"):
        email_pipeline.review(db, msg.id, "u-admin", "INVENTADA")


def test_quality_claim_opens_case_with_lot_after_human_confirmation(db, world):
    msg, _ = email_pipeline.process_raw(db, raw("<q1>", "compras@cc.example", "Reclamación",
                                                "Inconformidad: materia extraña en el lote L-555 de comino"))
    assert msg.classification.review_status == "needs_review"
    assert db.scalars(select(Case)).all() == []  # nada automático
    email_pipeline.review(db, msg.id, "u-calidad")
    res = email_pipeline.apply_suggestion(db, msg.id, "u-calidad")
    case = db.get(Case, res["entity_id"])
    assert case.type == "reclamacion_calidad" and case.lot_reference == "L-555" and case.account_id == world["acc"].id


def test_open_case_without_link_fails(db):
    msg, _ = email_pipeline.process_raw(db, raw("<q2>", "desconocido@x.example", "Docs", "Necesitamos la ficha técnica del comino"))
    email_pipeline.review(db, msg.id, "u-calidad")
    with pytest.raises(DomainError, match="crea el lead primero"):
        email_pipeline.apply_suggestion(db, msg.id, "u-calidad", "abrir_caso")


def test_apply_task_for_order_email(db, world):
    msg, _ = email_pipeline.process_raw(db, raw("<o1>", "compras@cc.example", "OC-9",
                                                "Adjunto orden de compra OC-9001, favor de surtir 1 tonelada de arroz. Urgente"))
    assert msg.classification.category == "PEDIDO" and msg.classification.review_status == "auto"
    res = email_pipeline.apply_suggestion(db, msg.id, "u-administracion")
    t = db.get(Task, res["entity_id"])
    assert t.assignee_role == "administracion" and t.priority == "alta" and t.origin == "sugerencia_correo"


def test_supplier_email_routed_outside_crm(db):
    msg, _ = email_pipeline.process_raw(db, raw("<p1>", "ventas@especias-origen-demo.com", "Oferta", "Les ofrecemos comino de nueva cosecha"))
    c = msg.classification
    assert c.category == "PROVEEDOR_COMPRAS" and c.suggested_action == "reenviar_fuera_crm" and c.crm_link_type is None
    assert email_pipeline.apply_suggestion(db, msg.id, "u-admin") == {"action": "reenviar_fuera_crm"}


def test_eml_parsing_html_attachment_and_directory(tmp_path):
    m = PyEmail()
    m["From"] = '"Ana" <Ana@Hotel.example>'
    m["Subject"] = "Cotización"
    m["Message-ID"] = "<x1@hotel.example>"
    m.set_content("<p>Hola, <b>cotización</b> de comino</p>", subtype="html")
    m.add_attachment(b"data", maintype="application", subtype="pdf", filename="a.pdf")
    (tmp_path / "a.eml").write_bytes(bytes(m))
    r = parse_eml_bytes(bytes(m))
    assert r.from_email == "ana@hotel.example" and r.from_name == "Ana" and r.has_attachments and "cotización" in r.body
    assert len(EmlDirectoryProvider(tmp_path).fetch()) == 1
    no_id = parse_eml_bytes(b"From: a@b.example\nSubject: s\n\nbody")
    assert no_id.message_id.startswith("<sha256-")


def test_gmail_provider_is_explicitly_not_implemented():
    with pytest.raises(NotImplementedError):
        GmailProvider()


def test_api_email_contract(admin, db):
    r = admin.post("/api/emails/ingest", json=[{"message_id": "<api1>", "from_email": "x@nuevo.example",
                                                "subject": "Cotización", "body": "cotizar 700 kg de pimienta"}])
    assert r.status_code == 200 and r.json()["new"] == 1
    e = admin.get("/api/emails").json()[0]
    for key in ["classification", "confidence", "extracted_entities", "suggested_owner", "suggested_action", "crm_entity_link"]:
        assert key in e
    assert admin.post("/api/emails/ingest", json={"no": "lista"}).status_code == 422
    assert admin.post("/api/emails/ingest", json=[{"from_email": "a@b.example"}]).status_code == 422
