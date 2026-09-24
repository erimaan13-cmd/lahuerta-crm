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
from app.services.automations import run_reorder_check

DEMO_PASSWORD = "demo1234"  # contraseña de demostración, pública a propósito; cambiar fuera de la demo

USERS = [
    ("admin@demo.local", "Admin Demo", "admin"),
    ("director@demo.local", "Dirección General Demo (administrador principal)", "admin"),
    ("ventas1@demo.local", "Vendedora Industrial Demo", "ventas"),
    ("ventas2@demo.local", "Vendedor Demo", "ventas"),
    ("atencion@demo.local", "Atención Demo", "atencion"),
    ("calidad@demo.local", "Calidad Demo", "calidad"),
    ("admon@demo.local", "Administración Demo", "administracion"),
    ("almacen@demo.local", "Almacén Demo", "almacen"),
    ("compras@demo.local", "Abastecimiento Demo", "abastecimiento"),
    ("rrhh@demo.local", "Recursos Humanos Demo", "rrhh"),
    ("taller@demo.local", "Mantenimiento Demo", "mantenimiento"),
    ("direccion@demo.local", "Dirección (lectura) Demo", "lectura"),
]
# Unidad de manejo y mínimos del catálogo demo (E-02): sku → (unidad, kg por unidad, empaque, mínimo, vida útil)
PRODUCT_SETUP = {
    "ESP-001": ("saco", 25, "saco_kraft", 300, 540), "ESP-002": ("caja", 10, "caja_corrugado", 120, 720),
    "ESP-003": ("saco", 20, "saco_kraft", 200, 365), "CHI-001": ("saco", 25, "saco_pp", 250, 365),
    "CHI-002": ("saco", 25, "saco_pp", 150, 365), "GRA-001": ("saco", 50, "saco_pp", 1000, 365),
    "GRA-002": ("saco", 50, "saco_pp", 800, 365), "SEM-001": ("saco", 25, "saco_kraft", 150, 270),
    "CON-001": ("caja", 15, "caja_corrugado", 100, 540),
}
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
        ErpOrder("P-54810", "C-004", "entregado", now - timedelta(days=96), now - timedelta(days=95), 5000),
        ErpOrder("P-54990", "C-004", "entregado", now - timedelta(days=61), now - timedelta(days=60), 4800),  # recompra vencida
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
        unit, kgu, pack, minimo, vida = PRODUCT_SETUP.get(sku, ("kg", 1, "granel", None, None))
        p = Product(sku=sku, name=name, category=cat, keywords=kw, unit=unit, kg_per_unit=kgu,
                    packaging=pack, min_stock_kg=minimo, shelf_life_days=vida)
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
    a6 = account("Alimentos Procesados del Bajío", "apbajio.example", "industria_alimentaria", "Querétaro", "Querétaro", "C-004", key=True)
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
    out = {"users": len(USERS), "erp_sync": stats, "reorder": run_reorder_check(db, adm)}
    out["operacion"] = seed_operations(db, users, prods, {"a1": a1, "a3": a3, "a6": a6})
    if with_emails:
        data_dir = config.BASE_DIR / "data"
        out["emails_mock"] = email_pipeline.ingest(db, MockMailboxProvider(data_dir / "demo_emails.json"), actor_id=adm)
        out["emails_eml"] = email_pipeline.ingest(db, EmlDirectoryProvider(data_dir / "sample_emails"), actor_id=adm)
    return out


def seed_operations(db: Session, users: dict, prods: dict, accs: dict) -> dict:
    """Datos demo de la operación interna: inventario, compras, pedidos, personal, caja y mantenimiento.

    Todo es sintético y está marcado "(DEMO)". Se arma con los mismos servicios que usa la interfaz,
    así que la bitácora queda igual que si alguien lo hubiera capturado a mano.
    """
    from app.services import (files as files_svc, hr, inventory as inv, maintenance as mnt,
                              notifications as notif, pettycash as caja, procurement as proc, sales)
    now = utcnow()
    adm = users["admin@demo.local"].id
    alm = users["almacen@demo.local"].id
    cmp_ = users["compras@demo.local"].id
    rh = users["rrhh@demo.local"].id
    tal = users["taller@demo.local"].id
    adn = users["admon@demo.local"].id

    # --- bodegas y proveedores
    w1 = inv.create_warehouse(db, {"code": "MTY", "name": "Bodega Guadalupe (DEMO)",
                                   "address": "Guadalupe, N.L."}, alm)
    w2 = inv.create_warehouse(db, {"code": "PAT", "name": "Patio de maniobras (DEMO)"}, alm)
    s1 = proc.create_supplier(db, {"name": "Especias de Origen (DEMO)", "origin": "nacional",
                                   "email": "ventas@especiasorigen.example", "phone": "8110000101",
                                   "contact_name": "Ing. Nayeli Ponce (DEMO)"}, cmp_)
    s2 = proc.create_supplier(db, {"name": "Importadora del Pacífico (DEMO)", "origin": "importado",
                                   "email": "orders@importpacifico.example"}, cmp_)

    # --- existencia inicial: un lote por producto, uno próximo a caducar y uno bajo mínimo
    lotes = {}
    for sku, kg, dias_caduca in [("ESP-001", 900, 400), ("ESP-002", 260, 700), ("ESP-003", 120, 20),
                                 ("CHI-001", 700, 300), ("GRA-001", 3200, 300), ("GRA-002", 1500, 300),
                                 ("SEM-001", 90, 150), ("CON-001", 220, 500)]:
        lot = inv.create_lot(db, {"product_id": prods[sku].id, "code": f"L-{sku[-3:]}-{now:%y%m}",
                                  "expires_on": (now + timedelta(days=dias_caduca)).date().isoformat(),
                                  "supplier_id": s1.id, "notes": "Lote de demostración"}, alm)
        lotes[sku] = lot
        inv.move(db, type="entrada", product_id=prods[sku].id, warehouse_id=w1.id, qty_kg=kg,
                 lot_id=lot.id, reason="Existencia inicial (DEMO)", ref_type="manual", actor_id=alm)
    # SEM-001 (mínimo 150 kg) queda en 90 kg → dispara la alerta de bajo mínimo

    # --- abastecimiento: una orden recibida, una por autorizar y una autorizada pendiente de recibir
    po1 = proc.create_order(db, {"supplier_id": s1.id, "warehouse_id": w1.id,
                                 "expected_date": (now + timedelta(days=3)).date().isoformat(),
                                 "notes": "Resurtido mensual (DEMO)"},
                            [{"product_id": prods["SEM-001"].id, "qty_kg": 500, "unit_cost_mxn": 38},
                             {"product_id": prods["ESP-003"].id, "qty_kg": 300, "unit_cost_mxn": 72}], cmp_)
    proc.submit(db, po1.id, cmp_)
    proc.authorize(db, po1.id, adm)
    proc.receive(db, po1.id, [{"item_id": po1.items[0].id, "qty_kg": 500, "lot_code": f"L-SEM-{now:%y%m}B",
                               "expires_on": (now + timedelta(days=240)).date().isoformat()}],
                 alm, supplier_invoice="A-10233 (DEMO)")
    po2 = proc.create_order(db, {"supplier_id": s2.id, "warehouse_id": w1.id,
                                 "expected_date": (now + timedelta(days=20)).date().isoformat()},
                            [{"product_id": prods["ESP-002"].id, "qty_kg": 1200, "unit_cost_mxn": 145}], cmp_)
    proc.submit(db, po2.id, cmp_)  # supera el umbral → queda por autorizar
    po3 = proc.create_order(db, {"supplier_id": s1.id, "warehouse_id": w1.id},
                            [{"product_id": prods["CHI-001"].id, "qty_kg": 400, "unit_cost_mxn": 61}], cmp_)
    proc.submit(db, po3.id, cmp_)

    # --- pedidos: uno entregado (descuenta inventario) y uno confirmado por entregar
    ped1 = sales.create_order(db, {"account_id": accs["a1"].id, "warehouse_id": w1.id,
                                   "promised_date": (now - timedelta(days=2)).date().isoformat(),
                                   "is_demo": True, "notes": "Entrega en andén (DEMO)"},
                              [{"product_id": prods["ESP-001"].id, "qty_kg": 250, "unit_price_mxn": 112},
                               {"product_id": prods["GRA-001"].id, "qty_kg": 800, "unit_price_mxn": 27}],
                              users["ventas1@demo.local"].id)
    sales.confirm(db, ped1.id, users["ventas1@demo.local"].id)
    sales.deliver(db, ped1.id, alm)
    sales.set_invoice(db, ped1.id, "F-8842 (DEMO)", adn)
    ped2 = sales.create_order(db, {"account_id": accs["a3"].id, "warehouse_id": w1.id,
                                   "promised_date": (now + timedelta(days=4)).date().isoformat(), "is_demo": True},
                              [{"product_id": prods["CHI-001"].id, "qty_kg": 300, "unit_price_mxn": 96}],
                              users["ventas2@demo.local"].id)
    sales.confirm(db, ped2.id, users["ventas2@demo.local"].id)

    # --- personal: dos puestos y tres empleados, uno con contrato por vencer
    pto1 = hr.create_job_profile(db, {"title": "Auxiliar de almacén (DEMO)", "area": "Almacén",
                                      "duties": "Recibir y acomodar materia prima\nSurtir pedidos\nRegistrar lotes y caducidades",
                                      "requirements": "Bachillerato\nManejo de montacargas\nCurso de inocuidad vigente"}, rh)
    pto2 = hr.create_job_profile(db, {"title": "Operador de molienda (DEMO)", "area": "Producción",
                                      "duties": "Operar el molino\nRegistrar parámetros del proceso\nLimpieza y sanitización",
                                      "requirements": "Secundaria\nExperiencia en alimentos\nBuenas prácticas de manufactura"}, rh)
    e1 = hr.create_employee(db, {"employee_no": "EMP-001", "full_name": "Juan Pérez (DEMO)",
                                 "job_profile_id": pto1.id, "hired_on": (now - timedelta(days=400)).date().isoformat(),
                                 "phone": "8110000201", "email": "jperez@demo.local"}, rh)
    e2 = hr.create_employee(db, {"employee_no": "EMP-002", "full_name": "María Soto (DEMO)",
                                 "job_profile_id": pto2.id, "hired_on": (now - timedelta(days=120)).date().isoformat(),
                                 "phone": "8110000202"}, rh)
    hr.create_employee(db, {"employee_no": "EMP-003", "full_name": "Luis Ramírez (DEMO)",
                            "job_profile_id": pto1.id, "hired_on": (now - timedelta(days=30)).date().isoformat()}, rh)
    hr.add_contract(db, e1.id, {"type": "indeterminado",
                                "start_on": (now - timedelta(days=400)).date().isoformat()}, rh)
    hr.add_contract(db, e2.id, {"type": "temporal", "start_on": (now - timedelta(days=120)).date().isoformat(),
                                "end_on": (now + timedelta(days=45)).date().isoformat()}, rh)  # dispara aviso semanal

    # --- caja chica con un gasto comprobado
    fondo = caja.create_fund(db, {"name": "Caja chica oficina (DEMO)", "fund_amount_mxn": 5000,
                                  "responsible_user_id": adn}, adm)
    ticket = files_svc.save_upload(db, "petty_cash", fondo.id, "ticket-demo.txt",
                                   b"Ticket de demostracion (DEMO). Documento sintetico.", adn,
                                   kind="comprobante", title="Ticket gasolina (DEMO)")
    caja.add_expense(db, fondo.id, {"category": "combustible", "amount_mxn": 850,
                                    "description": "Gasolina camioneta de reparto (DEMO)"}, adn,
                     receipt_id=ticket.id)
    caja.add_replenishment(db, fondo.id, {"amount_mxn": 850, "description": "Reposición del fondo (DEMO)"}, adm)

    # --- mantenimiento: camión con plan por kilometraje y clima con plan por meses
    cam = mnt.create_asset(db, {"code": "CAM-01", "name": "Camión de reparto 3.5 t (DEMO)", "type": "camion",
                                "brand": "Marca Demo", "model": "2019", "identifier": "ABC-123-XY",
                                "location": "Patio", "odometer_km": 84200,
                                "purchased_on": (now - timedelta(days=1400)).date().isoformat()}, tal)
    clima = mnt.create_asset(db, {"code": "CLI-01", "name": "Clima de oficina 2 t (DEMO)", "type": "clima",
                                  "location": "Oficinas", "hours_used": 2100}, tal)
    mnt.assign(db, cam.id, tal, user_id=tal)
    mnt.create_plan(db, cam.id, {"name": "Cambio de aceite y filtros", "kind": "preventivo",
                                 "freq_km": 10000, "freq_days": 180, "last_done_km": 76000,
                                 "last_done_on": (now - timedelta(days=150)).date().isoformat(),
                                 "assignee_user_id": tal}, tal)
    mnt.create_plan(db, clima.id, {"name": "Limpieza de serpentín", "kind": "preventivo", "freq_days": 90,
                                   "last_done_on": (now - timedelta(days=85)).date().isoformat()}, tal)
    files_svc.save_upload(db, "asset", cam.id, "poliza-demo.txt",
                          b"Poliza de garantia de demostracion (DEMO).", tal, kind="poliza_garantia",
                          title="Póliza de garantía (DEMO)",
                          expires_on=(now + timedelta(days=20)).date().isoformat())
    wo = mnt.create_work_order(db, {"asset_id": clima.id, "kind": "correctivo", "provider": "externo",
                                    "provider_name": "Servicios Clima del Norte (DEMO)",
                                    "description": "Fuga de gas refrigerante (DEMO)"}, tal)
    mnt.close_work_order(db, wo.id, {"cost_mxn": 2400, "done_on": (now - timedelta(days=3)).date().isoformat(),
                                     "notes": "Se recargó gas y se cambió válvula (DEMO)"}, tal)

    avisos = notif.generate(db, adm)
    return {"bodegas": 2, "proveedores": 2, "lotes": len(lotes) + 1, "compras": 3, "pedidos": 2,
            "empleados": 3, "activos": 2, "avisos": avisos["total"]}


def reset_and_seed() -> dict:
    Base.metadata.drop_all(bind=engine)
    init_db()
    _stamp_alembic_head()
    with SessionLocal() as db:
        return seed(db)


def _stamp_alembic_head():
    """La BD de demo se crea con create_all; se marca en la última migración para que
    `alembic upgrade head` funcione en adelante sin recrear tablas."""
    try:
        from alembic import command
        from alembic.config import Config
        cfg = Config(str(config.BASE_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(config.BASE_DIR / "migrations"))
        command.stamp(cfg, "head")
    except ImportError:  # alembic es opcional para la demo
        pass


if __name__ == "__main__":
    import json
    print(json.dumps(reset_and_seed(), indent=2, ensure_ascii=False, default=str))
