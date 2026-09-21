"""Datos de DEMOSTRACIÓN 100 % sintéticos (RF-23).

NINGUNA empresa, persona, correo, teléfono o pedido de este archivo es cliente o dato real de
Empacadora La Huerta. Los dominios usan el sufijo reservado `.example` (RFC 2606) y los nombres de
empresa llevan "(DEMO)". El catálogo de productos es ilustrativo, dentro de las líneas publicadas
(especias, granos, semillas, chiles secos, condimentos — evidencia E09); la lista real es DESCONOCIDA.

Uso:  python -m app.seed        (borra y recrea data/crm.db)
"""
from datetime import timedelta

from sqlalchemy.orm import Session

from app import config
from app.db import Base, SessionLocal, engine, init_db
from app.integrations.email_providers import EmlDirectoryProvider, MockMailboxProvider
from app.integrations.erp import ErpOrder, MockErpAdapter, sync_orders
from app.models import Account, Contact, Product, Sector, User, utcnow
from app.security import hash_password
from app.services import crm, email_pipeline

DEMO_PASSWORD = "demo1234"  # contraseña de demostración, pública a propósito; cambiar fuera de la demo

USERS = [
    ("admin@demo.local", "Admin Demo", "admin"),
    ("ventas1@demo.local", "Vendedora Industrial Demo", "ventas"),
    ("ventas2@demo.local", "Vendedor Demo", "ventas"),
    ("atencion@demo.local", "Atención Demo", "atencion"),
    ("calidad@demo.local", "Calidad Demo", "calidad"),
    ("admon@demo.local", "Administración Demo", "administracion"),
    ("direccion@demo.local", "Dirección (lectura) Demo", "lectura"),
]
SECTORS = [("industria_alimentaria", "Industria alimentaria"), ("hotel", "Hotel"),
           ("restaurante", "Restaurante / cadena"), ("comedor_industrial", "Comedor industrial"),
           ("otro", "Otro")]
PRODUCTS = [  # sku, nombre, categoría, sinónimos
    ("ESP-001", "Comino molido", "especia", "comino"),
    ("ESP-002", "Pimienta negra", "especia", "pimienta"),
    ("ESP-003", "Orégano", "especia", "oregano"),
    ("ESP-004", "Canela", "especia", "canela en raja,canela molida"),
    ("ESP-005", "Pimentón / paprika", "especia", "pimenton,paprika"),
    ("ESP-006", "Ajo en polvo", "especia", "ajo"),
    ("CHI-001", "Chile guajillo", "chile_seco", "guajillo"),
    ("CHI-002", "Chile ancho", "chile_seco", "ancho"),
    ("CHI-003", "Chile de árbol", "chile_seco", "chile de arbol"),
    ("GRA-001", "Arroz", "grano", "arroz"),
    ("GRA-002", "Frijol pinto", "grano", "frijol"),
    ("SEM-001", "Ajonjolí", "semilla", "ajonjoli,sesamo"),
    ("CON-001", "Sazonador para carnes", "condimento", "sazonador,sazonador para carne"),
    ("CON-002", "Adobo base", "condimento", "adobo"),
]


def demo_erp_orders() -> list[ErpOrder]:
    now = utcnow()
    return [
        ErpOrder("P-55101", "C-001", "entregado", now - timedelta(days=40), now - timedelta(days=39), 1500),
        ErpOrder("P-55107", "C-001", "entregado", now - timedelta(days=12), now - timedelta(days=11), 1200),
        ErpOrder("P-55120", "C-002", "enviado", now + timedelta(days=1), None, 800),
        ErpOrder("P-55124", "C-003", "en_surtido", now + timedelta(days=2), None, 2000),
        ErpOrder("P-55999", "C-999", "recibido", now + timedelta(days=3), None, 600),  # sin cuenta → error controlado
    ]


def seed(db: Session, with_emails: bool = True) -> dict:
    users = {}
    for email, name, role in USERS:
        u = User(email=email, full_name=name, role=role, team=role, password_hash=hash_password(DEMO_PASSWORD))
        db.add(u)
        users[email] = u
    for code, name in SECTORS:
        db.add(Sector(code=code, name=name))
    prods = {}
    for sku, name, cat, kw in PRODUCTS:
        p = Product(sku=sku, name=name, category=cat, keywords=kw)
        db.add(p)
        prods[sku] = p
    db.commit()
    v1, v2, adm = users["ventas1@demo.local"].id, users["ventas2@demo.local"].id, users["admin@demo.local"].id

    def account(name, dom, sector, city, state, erp=None, key=False, owner=v1):
        a = Account(name=f"{name} (DEMO)", domain=dom, sector_code=sector, city=city, state=state,
                    erp_customer_ref=erp, is_key_account=key, owner_id=owner, is_demo=True)
        db.add(a)
        db.flush()
        return a

    def contact(acc, name, email, phone, title, primary=True):
        c = Contact(account_id=acc.id, full_name=name, email=email, phone=phone, job_title=title, is_primary=primary)
        db.add(c)
        db.flush()
        return c

    a1 = account("Restaurantes Sabor Norteño", "sabornorteno.example", "restaurante", "Monterrey", "Nuevo León", "C-001", True)
    a2 = account("Hotel Sierra Madre Plaza", "sierramadreplaza.example", "hotel", "San Pedro Garza García", "Nuevo León", "C-002")
    a3 = account("Comedores Industriales del Norte", "comedoresnorte.example", "comedor_industrial", "Apodaca", "Nuevo León", "C-003")
    a4 = account("Botanas y Embutidos Regios", "botanasregias.example", "industria_alimentaria", "Guadalupe", "Nuevo León", owner=v2)
    a5 = account("Grupo Taquero El Fogón", "elfogon.example", "restaurante", "Saltillo", "Coahuila", owner=v2)
    a6 = account("Alimentos Procesados del Bajío", "apbajio.example", "industria_alimentaria", "Querétaro", "Querétaro", key=True)
    c1 = contact(a1, "Laura Méndez (DEMO)", "compras@sabornorteno.example", "8110000001", "Jefa de compras")
    c2 = contact(a2, "Jorge Salinas (DEMO)", "chef@sierramadreplaza.example", "8110000002", "Chef ejecutivo")
    c3 = contact(a3, "Patricia Garza (DEMO)", "calidad@comedoresnorte.example", "8110000003", "Coordinadora de calidad")
    contact(a4, "Ricardo Treviño (DEMO)", "desarrollo@botanasregias.example", "8110000004", "Desarrollo de producto")
    contact(a5, "Héctor Cantú (DEMO)", "operaciones@elfogon.example", "8440000005", "Gerente de operaciones")
    contact(a6, "Sofía Ramírez (DEMO)", "aseguramiento@apbajio.example", "4420000006", "Aseguramiento de calidad")
    db.commit()

    # Oportunidades en distintas etapas
    o1 = crm.create_opportunity(db, {"account_id": a1.id, "contact_id": c1.id, "title": "Resurtido trimestral comino y arroz",
                                     "type": "recompra", "est_volume_kg": 2500, "product_ids": [prods["ESP-001"].id, prods["GRA-001"].id],
                                     "is_demo": True, "owner_id": v1}, adm)
    crm.create_quote(db, o1.id, [{"product_id": prods["ESP-001"].id, "qty_kg": 1000, "packaging": "saco_kraft_pe", "unit_price_mxn": 98.5},
                                 {"product_id": prods["GRA-001"].id, "qty_kg": 1500, "packaging": "saco_pp_pead", "unit_price_mxn": 24.0}], adm)
    crm.change_stage(db, o1.id, "cotizacion", adm)
    crm.change_stage(db, o1.id, "negociacion", adm)

    o2 = crm.create_opportunity(db, {"account_id": a4.id, "title": "Sazonador chipotle-limón para botanas", "type": "formula_personalizada",
                                     "est_volume_kg": 3000, "product_ids": [prods["CON-001"].id], "is_demo": True, "owner_id": v2}, adm)
    crm.change_stage(db, o2.id, "desarrollo_formula", adm)
    crm.change_stage(db, o2.id, "muestra_enviada", adm)

    o3 = crm.create_opportunity(db, {"account_id": a5.id, "title": "Chiles secos para 12 sucursales", "type": "estandar",
                                     "est_volume_kg": 900, "product_ids": [prods["CHI-001"].id, prods["CHI-002"].id], "is_demo": True, "owner_id": v2}, adm)
    o4 = crm.create_opportunity(db, {"account_id": a2.id, "contact_id": c2.id, "title": "Especias para banquetes temporada alta",
                                     "type": "estandar", "est_volume_kg": 800, "product_ids": [prods["ESP-002"].id, prods["ESP-003"].id],
                                     "is_demo": True}, adm)
    crm.create_quote(db, o4.id, [{"product_id": prods["ESP-002"].id, "qty_kg": 500, "packaging": "caja_corrugado", "unit_price_mxn": 185}], adm)
    crm.change_stage(db, o4.id, "cotizacion", adm)
    crm.change_stage(db, o4.id, "ganada", adm)
    o5 = crm.create_opportunity(db, {"account_id": a6.id, "title": "Pimentón para línea de embutidos", "type": "estandar",
                                     "est_volume_kg": 5000, "product_ids": [prods["ESP-005"].id], "is_demo": True}, adm)
    crm.change_stage(db, o5.id, "perdida", adm, lost_reason="Precio por encima del proveedor actual (DEMO)")
    o6 = crm.create_opportunity(db, {"account_id": a3.id, "title": "Abasto mensual orégano y frijol", "type": "recompra",
                                     "est_volume_kg": 2000, "product_ids": [prods["ESP-003"].id, prods["GRA-002"].id], "is_demo": True}, adm)
    _ = (o3, o6)

    # Casos
    crm.create_case(db, {"type": "reclamacion_calidad", "severity": "alta", "subject": "Humedad en sacos de orégano (DEMO)",
                         "account_id": a3.id, "contact_id": c3.id, "lot_reference": "L-2609-114", "is_demo": True}, adm)
    crm.create_case(db, {"type": "documentacion", "severity": "baja", "subject": "Solicitud de ficha técnica de pimentón (DEMO)",
                         "account_id": a6.id, "is_demo": True}, adm)

    # Leads
    leads = [
        {"full_name": "Mariana López (DEMO)", "company_name": "Cocina Económica La Esperanza (DEMO)", "email": "mariana@laesperanza.example",
         "phone": "8120000011", "city": "Monterrey", "sector_code": "restaurante", "product_interest_text": "Comino y pimienta",
         "volume_band": "500kg_1t", "source": "web_contacto", "message": "Quiero cotizar un pedido mensual."},
        {"full_name": "Daniel Ortiz (DEMO)", "company_name": "Planta Cárnica Ortiz (DEMO)", "email": "dortiz@carnicaortiz.example",
         "city": "Monterrey", "sector_code": "industria_alimentaria", "volume_band": "mas_1t", "source": "web_catalogo"},
        {"full_name": "Fernanda Ruiz (DEMO)", "company_name": "Hotel Boutique Río (DEMO)", "email": "fruiz@hotelrio.example",
         "phone": "8120000013", "city": "Santiago", "sector_code": "hotel", "est_volume_kg": 300, "source": "google_ads",
         "campaign": "search-especias-industriales", "product_interest_text": "Orégano"},
        {"full_name": "Óscar Vela (DEMO)", "company_name": "Comedor Planta Norte (DEMO)", "phone": "81 2000 0014",
         "city": "Escobedo", "sector_code": "comedor_industrial", "source": "whatsapp", "est_volume_kg": 1200,
         "product_interest_text": "Arroz y frijol"},
        {"full_name": "Roberto Vela (DEMO)", "company_name": "Comedor Planta Norte (DEMO)", "phone": "+52 81 2000 0014",
         "sector_code": "comedor_industrial", "source": "telefono"},  # mismo teléfono → posible duplicado
        {"full_name": "Ana Paula Cruz (DEMO)", "company_name": "Taquería El Güero (DEMO)", "email": "anapaula.cruz@gmail.com",
         "sector_code": "restaurante", "est_volume_kg": 60, "source": "meta_ads", "product_interest_text": "Chile de árbol"},
        {"full_name": "Iván Robles (DEMO)", "company_name": "Industrias Robles (DEMO)", "email": "irobles@roblesind.example",
         "sector_code": "industria_alimentaria", "source": "linkedin", "est_volume_kg": 2500,
         "product_interest_text": "Sazonador personalizado", "message": "Buscamos desarrollar un sazonador para marca propia."},
    ]
    created = []
    for i, data in enumerate(leads):
        data["is_demo"] = True
        data["owner_id"] = v1 if i % 2 == 0 else v2
        lead, _ = crm.create_lead(db, data, adm)
        created.append(lead)
    crm.log_activity(db, {"type": "llamada", "subject": "Primer contacto: interesada en entregas mensuales",
                          "related_type": "lead", "related_id": created[0].id}, v1)
    crm.change_lead_status(db, created[0].id, "calificado", v1)
    crm.change_lead_status(db, created[1].id, "calificado", adm)
    crm.convert_lead(db, created[1].id, adm, opp_type="estandar", opp_title="Especias para embutidos — Planta Cárnica Ortiz (DEMO)")
    crm.change_lead_status(db, created[5].id, "descartado", v2, "Volumen menor al mínimo de 500 kg")

    stats = sync_orders(db, MockErpAdapter(demo_erp_orders()), adm)
    out = {"users": len(USERS), "erp_sync": stats}
    if with_emails:
        data_dir = config.BASE_DIR / "data"
        out["emails_mock"] = email_pipeline.ingest(db, MockMailboxProvider(data_dir / "demo_emails.json"), actor_id=adm)
        out["emails_eml"] = email_pipeline.ingest(db, EmlDirectoryProvider(data_dir / "sample_emails"), actor_id=adm)
    return out


def reset_and_seed() -> dict:
    Base.metadata.drop_all(bind=engine)
    init_db()
    with SessionLocal() as db:
        return seed(db)


if __name__ == "__main__":
    import json
    print(json.dumps(reset_and_seed(), indent=2, ensure_ascii=False, default=str))
