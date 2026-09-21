"""Evaluación del clasificador sobre el corpus SINTÉTICO de demostración (etiquetas asignadas a mano).
Advertencia: es el mismo corpus con el que se ajustaron las reglas → la cifra es optimista y NO
representa desempeño con correos reales. Uso: python -m scripts.eval_classifier (tras python -m app.seed)"""
from app.db import SessionLocal
from app.models import EmailMessage

GOLD = {
    "Cotización de especias": "SOLICITUD_COTIZACION", "Buscamos nuevo proveedor de especias": "LEAD_NUEVO",
    "Orden de compra OC-7781": "PEDIDO", "RE: COT-2026-0001": "SEGUIMIENTO_COMERCIAL",
    "Desarrollo de sazonador": "FORMULA_PERSONALIZADA", "Reclamación orégano lote L-2609-114": "CALIDAD_RECLAMACION",
    "Documentos para alta de proveedor": "DOCUMENTACION_CALIDAD", "Pedido P-55120 no ha llegado": "LOGISTICA_ENTREGA",
    "Proforma comino - embarque octubre": "PROVEEDOR_COMPRAS", "Factura y complemento de pago": "ADMIN_FACTURACION",
    "Posicionamiento web para su empresa": "SPAM_NO_RELEVANTE", "Hola": "OTRO",
    "Pedido incompleto": "CALIDAD_RECLAMACION", "precio pimienta": "SOLICITUD_COTIZACION",
    "Request for quotation - cumin": "SOLICITUD_COTIZACION", "Solicitud de cotización para 3 hoteles": "SOLICITUD_COTIZACION",
    "Pedimento y documentos de importación - ajonjolí": "PROVEEDOR_COMPRAS", "Precio por kg de frijol y arroz": "SOLICITUD_COTIZACION",
}

with SessionLocal() as db:
    rows = [(m.subject, m.classification) for m in db.query(EmailMessage) if m.subject in GOLD]
ok = sum(c.category == GOLD[s] for s, c in rows)
auto = [(s, c) for s, c in rows if c.review_status == "auto"]
auto_ok = sum(c.category == GOLD[s] for s, c in auto)
print(f"Correos evaluados: {len(rows)}")
print(f"Exactitud top-1 (todas): {ok}/{len(rows)} = {ok/len(rows):.0%}")
print(f"Auto-clasificados: {len(auto)} · correctos entre auto: {auto_ok}/{len(auto)}")
print(f"Enviados a Needs Review: {len(rows)-len(auto)}")
for s, c in rows:
    flag = "OK " if c.category == GOLD[s] else "ERR"
    print(f"  {flag} {s[:40]:40} pred={c.category:22} gold={GOLD[s]:22} conf={c.confidence:.2f} {c.review_status}")
