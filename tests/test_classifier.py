"""Clasificador desacoplado: categorías, confianza, revisión humana, extracción y paso híbrido (RF-11..13, RF-16)."""
import pytest

from app import config
from app.classifier import engine, normalize
from app.classifier.extract import CatalogItem, extract_all, extract_quantities
from app.classifier.llm import MockLLMClient

CAT = [CatalogItem("ESP-001", "ESP-001", "Comino molido", ["comino"]),
       CatalogItem("ESP-002", "ESP-002", "Pimienta negra", ["pimienta"]),
       CatalogItem("CHI-001", "CHI-001", "Chile guajillo", ["guajillo"]),
       CatalogItem("GRA-001", "GRA-001", "Arroz", ["arroz"])]


def run(subject, body, sender="x@nuevo.example", kind="desconocido", llm=None):
    return engine.classify(engine.ClassifierInput(subject, body, sender, None, kind, CAT), llm=llm)


@pytest.mark.parametrize("subject,body,kind,expected", [
    ("Cotización", "Somos un restaurante, me pueden cotizar 600 kg de guajillo?", "desconocido", "SOLICITUD_COTIZACION"),
    ("Proveedor", "Buscamos un nuevo proveedor de especias, me interesa su catálogo", "desconocido", "LEAD_NUEVO"),
    ("OC 1234", "Adjunto orden de compra OC-1234, favor de surtir 20 sacos de comino", "contacto", "PEDIDO"),
    ("RE: propuesta", "Respecto a la cotización COT-2026-0003, ¿pueden mejorar el precio?", "contacto", "SEGUIMIENTO_COMERCIAL"),
    ("Sazonador", "Queremos un sazonador personalizado con perfil de sabor ahumado, enviar muestras", "desconocido", "FORMULA_PERSONALIZADA"),
    ("Queja", "Encontramos materia extraña en el lote L-77 de pimienta", "contacto", "CALIDAD_RECLAMACION"),
    ("Docs", "Necesitamos la ficha técnica y el certificado de análisis del comino", "contacto", "DOCUMENTACION_CALIDAD"),
    ("Entrega", "El pedido no ha llegado, ¿cuál es la fecha de entrega?", "contacto", "LOGISTICA_ENTREGA"),
    ("Proforma", "Adjuntamos proforma del contenedor, condiciones FOB", "proveedor", "PROVEEDOR_COMPRAS"),
    ("Factura", "Favor de enviar la factura XML y el complemento de pago", "contacto", "ADMIN_FACTURACION"),
    ("Oferta", "Posicionamiento web SEO, oferta limitada, haz clic. Darse de baja aquí", "desconocido", "SPAM_NO_RELEVANTE"),
])
def test_categories(subject, body, kind, expected):
    r = run(subject, body, kind=kind)
    assert r.classification == expected, (r.scores, r.evidence)
    assert 0.0 <= r.confidence <= 1.0


def test_no_signal_goes_to_needs_review_as_other():
    r = run("Hola", "¿Me pueden llamar?")
    assert r.classification == "OTRO" and r.confidence == 0 and r.needs_review


def test_quality_claim_always_needs_review_even_with_high_confidence():
    r = run("Reclamación", "Inconformidad: producto contaminado con insectos en el lote L-1", kind="contacto")
    assert r.confidence >= config.CLASSIFIER_THRESHOLD and r.needs_review
    assert "sensible" in r.review_reason and r.suggested_owner == "calidad" and r.suggested_action == "abrir_caso"


def test_ambiguous_mixed_email_needs_review_by_margin():
    r = run("Pedido incompleto", "Llegó incompleto, un saco con humedad y la factura con otro importe", kind="contacto")
    assert r.needs_review and "margen" in (r.review_reason or "")


def test_english_quote_is_recognized_since_v1_1():
    r = run("Request for quotation", "We would like a quotation for 2 tons of ground cumin")
    assert r.classification == "SOLICITUD_COTIZACION"


def test_unsupported_language_is_not_forced_into_a_category():
    r = run("Pedido de proposta", "Gostaríamos de receber uma proposta para cominho moído")
    assert r.needs_review  # portugués: sin reglas → revisión humana


@pytest.mark.parametrize("subject,body,kind,expected", [
    ("RE: Propuesta", "Gracias por la propuesta, ¿el precio es negociable si subimos volumen?", "contacto", "SEGUIMIENTO_COMERCIAL"),
    ("Pedido + factura", "Favor de surtir 1,200 kg de arroz y mandar la factura con el nuevo RFC", "contacto", "PEDIDO"),
    ("Entrega y producto", "Llegó tarde y los costales venían rotos y mojados", "contacto", "CALIDAD_RECLAMACION"),
    ("Aviso", "Su cuenta ha sido suspendida, verifique sus datos. Factura pendiente", "desconocido", "SPAM_NO_RELEVANTE"),
    ("Automatic reply: PO 12", "I am out of the office until Monday", "contacto", "OTRO"),
    ("Estado de cuenta", "Le enviamos su estado de cuenta con saldo vencido", "proveedor", "PROVEEDOR_COMPRAS"),
])
def test_mixed_email_priority_rules(subject, body, kind, expected):
    assert run(subject, body, kind=kind).classification == expected


def test_known_sender_is_never_new_lead():
    r = run("Info", "Me interesa más información de su catálogo", kind="contacto")
    assert r.classification != "LEAD_NUEVO"


def test_new_sender_quote_suggests_create_lead_known_sender_suggests_task():
    assert run("Cotización", "cotizar 600 kg de arroz").suggested_action == "crear_lead"
    assert run("Cotización", "cotizar 600 kg de arroz", kind="contacto").suggested_action == "crear_tarea"


def test_extraction_fields():
    body = ("Buen día, desde Monterrey. Necesitamos 1,500 kg de comino y 2 toneladas de arroz, además 10 sacos de guajillo. "
            "Somos una planta de embutidos. Urgente. Cel. (81) 1234-5678. Alimentos del Norte S.A. de C.V. "
            "Ref. COT-2026-0007, pedido P-9912, lote L-2609-1, factura F-3321")
    e = extract_all("Pedido", body, "compras@adn.example", "Juan", CAT)
    assert e["city"] == "Monterrey" and e["state"] == "Nuevo León"
    assert e["sector"] == "industria_alimentaria" and e["urgency"] == "alta"
    assert e["phones"] == ["8112345678"]
    assert e["total_kg"] == 1500 + 2000 + 250
    assert {p["sku"] for p in e["products"]} == {"ESP-001", "GRA-001", "CHI-001"}
    assert e["company"].startswith("Alimentos del Norte S.A. de C.V") and e["company_source"] == "razon_social"
    refs = e["references"]
    assert refs["quote_folio"] == ["COT-2026-0007"] and "P-9912" in refs["order_ref"]
    assert refs["lot_ref"] == ["L-2609-1"] and refs["invoice_ref"] == ["F-3321"]


def test_extraction_edge_cases():
    assert extract_quantities("sin cantidades") == []
    assert extract_quantities("0.5 ton")[0]["kg"] == 500
    assert extract_quantities("3 cajas")[0]["kg"] is None  # unidad sin conversión conocida
    e = extract_all("", "", "persona@gmail.com", None, CAT)
    assert e["company"] is None and e["products"] == [] and e["total_kg"] is None and e["below_minimum"] is False
    assert extract_all("", "quiero 50 kg", "a@b.example", None, CAT)["below_minimum"] is True


def test_normalization_strips_html_and_quoted_history():
    raw = "<p>Hola <b>equipo</b></p><p>El lun, 1 sep 2026 a las 9:00, X escribió:</p><blockquote>&gt; factura vieja</blockquote>"
    clean = normalize.clean_body(raw)
    assert "Hola equipo" in clean and "factura" not in clean
    assert normalize.clean_body("texto\n> citado\nmás") == "texto\nmás"


def test_hybrid_llm_only_called_when_uncertain(monkeypatch):
    monkeypatch.setattr(config, "LLM_ENABLED", True)
    agree = MockLLMClient(("LEAD_NUEVO", 0.9))
    r = run("Hola", "¿Tienen comino?", llm=agree)
    assert agree.calls == 1 and r.method == "hybrid" and not r.needs_review
    disagree = MockLLMClient(("SPAM_NO_RELEVANTE", 0.95))
    r = run("Hola", "¿Tienen comino?", llm=disagree)
    assert r.needs_review and "llm=" in r.review_reason
    confident = MockLLMClient(("OTRO", 0.99))
    run("Factura", "Favor de enviar la factura XML y el complemento de pago", kind="contacto", llm=confident)
    assert confident.calls == 0  # alta confianza: no se gasta LLM


def test_llm_disabled_by_default():
    llm = MockLLMClient(("LEAD_NUEVO", 0.9))
    r = run("Hola", "¿Me pueden llamar?", llm=llm)
    assert llm.calls == 0 and r.method == "rules"
