"""PDF de cotización (RF-36) con ReportLab. Se genera al vuelo; el CRM no lo envía por correo."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app import config
from app.models import Quote
from app.services.business_time import to_local

PACKAGING_LABELS = {"saco_pp_pead": "Saco de polipropileno con bolsa PEAD",
                    "saco_kraft_pe": "Saco kraft triple capa con bolsa PE",
                    "caja_corrugado": "Caja de cartón corrugado"}


def render_quote_pdf(q: Quote) -> bytes:
    opp, acc = q.opportunity, q.opportunity.account
    demo = acc.is_demo or opp.is_demo
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                            bottomMargin=1.8 * cm, title=f"Cotización {q.folio}")
    st = getSampleStyleSheet()
    story = []
    if demo:
        story.append(Paragraph("<font color='#b42318'><b>DOCUMENTO DE DEMOSTRACIÓN — DATOS SINTÉTICOS, SIN VALIDEZ COMERCIAL</b></font>", st["Normal"]))
        story.append(Spacer(1, 6))
    story += [Paragraph(f"<b>{config.COMPANY_NAME}</b>", st["Title"]),
              Paragraph(f"Cotización <b>{q.folio}</b> · estado: {q.status}", st["Heading2"]),
              Paragraph(f"Fecha: {to_local(q.created_at):%d/%m/%Y} · Vigente hasta: {to_local(q.valid_until):%d/%m/%Y}"
                        if q.valid_until else f"Fecha: {to_local(q.created_at):%d/%m/%Y}", st["Normal"]),
              Paragraph(f"Cliente: <b>{acc.name}</b> · {acc.city or ''} {acc.state or ''}", st["Normal"]),
              Paragraph(f"Referencia: {opp.title}", st["Normal"]), Spacer(1, 12)]
    rows = [["Producto", "kg", "Empaque", "Precio/kg (MXN)", "Importe (MXN)"]]
    for it in q.items:
        rows.append([it.product.name, f"{it.qty_kg:,.0f}", PACKAGING_LABELS.get(it.packaging, it.packaging),
                     f"{it.unit_price_mxn:,.2f}", f"{it.qty_kg * it.unit_price_mxn:,.2f}"])
    rows.append(["Total", f"{q.total_kg:,.0f}", "", "", f"{q.total_mxn:,.2f}"])
    t = Table(rows, colWidths=[4.5 * cm, 2 * cm, 5.2 * cm, 2.8 * cm, 3 * cm], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8a3b12")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                           ("ALIGN", (1, 1), (1, -1), "RIGHT"), ("ALIGN", (3, 1), (4, -1), "RIGHT"),
                           ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                           ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc"))]))
    story += [t, Spacer(1, 14),
              Paragraph("Precios en pesos mexicanos, sin IVA. Venta mínima por volumen: 500 kg. "
                        "Condiciones de pago, flete y tiempos de entrega sujetos a confirmación.", st["Normal"])]
    doc.build(story)
    return buf.getvalue()
