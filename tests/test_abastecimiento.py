"""Abastecimiento: folio, autorización por monto, recepción que da de alta lote y entrada de inventario,
cancelación, precios, permisos y rastro en la bitácora."""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app import config
from app.models import AuditEvent, Lot, StockMovement, utcnow
from app.services import inventory, procurement
from app.services.common import DomainError
from tests.conftest import ui_post

COMPRAS = "u-abastecimiento"


def orden(db, kg=100.0, costo=50.0, product="ESP-001", warehouse="w-mty", actor=COMPRAS):
    return procurement.create_order(db, {"supplier_id": "sup-1", "warehouse_id": warehouse},
                                    [{"product_id": product, "qty_kg": kg, "unit_cost_mxn": costo}], actor)


def acciones(db, prefijo: str) -> list[str]:
    db.expire_all()
    return [e.action for e in db.scalars(select(AuditEvent).order_by(AuditEvent.seq))
            if e.action.startswith(prefijo)]


def fecha(dias: int) -> str:
    return (utcnow() + timedelta(days=dias)).date().isoformat()


# ------------------------------------------------------------------ alta
def test_folio_por_conteo_y_totales(db):
    po = orden(db, kg=100, costo=50)
    assert po.folio == "OC-0001" and po.status == "borrador"
    assert po.total_kg == 100.0 and po.total_mxn == 5000.0
    assert orden(db).folio == "OC-0002"


def test_alta_sin_renglones_o_con_datos_invalidos_se_rechaza(db):
    with pytest.raises(DomainError, match="al menos un renglón"):
        procurement.create_order(db, {"supplier_id": "sup-1"}, [], COMPRAS)
    with pytest.raises(DomainError, match="costo por kilo"):
        procurement.create_order(db, {"supplier_id": "sup-1"},
                                 [{"product_id": "ESP-001", "qty_kg": 10}], COMPRAS)
    with pytest.raises(DomainError, match="No se encontró Proveedor"):
        procurement.create_order(db, {"supplier_id": "nadie"},
                                 [{"product_id": "ESP-001", "qty_kg": 10, "unit_cost_mxn": 1}], COMPRAS)


# ------------------------------------------------------------------ autorización por monto (E-07)
def test_monto_bajo_se_autoriza_solo_y_monto_alto_pide_autorizacion(db):
    umbral = config.PO_AUTH_THRESHOLD_MXN
    baja = procurement.submit(db, orden(db, kg=10, costo=1).id, COMPRAS)
    assert baja.total_mxn <= umbral and baja.status == "autorizada" and baja.authorized_at is None

    alta = orden(db, kg=1000, costo=umbral)  # muy por arriba del umbral
    assert procurement.submit(db, alta.id, COMPRAS).status == "por_autorizar"
    autorizada = procurement.authorize(db, alta.id, "u-admin")
    assert autorizada.status == "autorizada" and autorizada.authorized_by == "u-admin"
    assert autorizada.authorized_at is not None


def test_transiciones_invalidas(db):
    po = orden(db)
    with pytest.raises(DomainError, match="por autorizar"):
        procurement.authorize(db, po.id, "u-admin")       # todavía en borrador
    procurement.submit(db, po.id, COMPRAS)                 # monto bajo → autorizada
    with pytest.raises(DomainError, match="borrador"):
        procurement.submit(db, po.id, COMPRAS)             # ya no es borrador


# ------------------------------------------------------------------ recepción
def test_flujo_completo_crear_enviar_autorizar_recibir(db):
    po = orden(db, kg=1000, costo=100)                      # 100 000 MXN: exige autorización
    assert procurement.submit(db, po.id, COMPRAS).status == "por_autorizar"
    procurement.authorize(db, po.id, "u-admin")
    item = po.items[0]
    po = procurement.receive(db, po.id, [{"item_id": item.id, "qty_kg": 1000, "lot_code": "l-oc-1",
                                          "expires_on": fecha(200)}], COMPRAS,
                             supplier_invoice="F-DEMO-77")
    assert po.status == "recibida" and po.received_at is not None and po.supplier_invoice == "F-DEMO-77"
    assert po.items[0].received_kg == 1000.0

    lote = db.scalar(select(Lot).where(Lot.code == "L-OC-1"))
    assert lote is not None and lote.supplier_id == "sup-1" and lote.expires_on.date().isoformat() == fecha(200)
    assert inventory.balance(db, "ESP-001", "w-mty") == 1000.0
    assert inventory.lot_balance(db, lote.id) == 1000.0
    mv = db.scalars(select(StockMovement).where(StockMovement.ref_type == "orden_compra")).one()
    assert mv.type == "entrada" and mv.ref_id == po.id and mv.qty_kg == 1000.0 and mv.actor_id == COMPRAS


def test_recepcion_parcial_deja_la_orden_abierta(db):
    po = orden(db, kg=200, costo=10)
    procurement.submit(db, po.id, COMPRAS)                  # monto bajo → autorizada
    item = po.items[0]
    po = procurement.receive(db, po.id, [{"item_id": item.id, "qty_kg": 80, "lot_code": "L-P1"}], COMPRAS)
    assert po.status == "autorizada" and po.items[0].received_kg == 80.0
    assert procurement.pending_kg(po) == 120.0
    assert inventory.balance(db, "ESP-001", "w-mty") == 80.0

    with pytest.raises(DomainError, match="solo faltan"):
        procurement.receive(db, po.id, [{"item_id": item.id, "qty_kg": 500, "lot_code": "L-P1"}], COMPRAS)

    po = procurement.receive(db, po.id, [{"item_id": item.id, "qty_kg": 120, "lot_code": "L-P1"}], COMPRAS)
    assert po.status == "recibida" and procurement.pending_kg(po) == 0.0
    assert inventory.balance(db, "ESP-001", "w-mty") == 200.0
    assert len(db.scalars(select(Lot).where(Lot.code == "L-P1")).all()) == 1  # el lote se reutiliza


def test_recepcion_exige_orden_autorizada_lote_y_kilos(db):
    po = orden(db, kg=50, costo=10)
    item = po.items[0]
    with pytest.raises(DomainError, match="autorizada"):
        procurement.receive(db, po.id, [{"item_id": item.id, "qty_kg": 10, "lot_code": "L-X"}], COMPRAS)
    procurement.submit(db, po.id, COMPRAS)
    with pytest.raises(DomainError, match="código de lote"):
        procurement.receive(db, po.id, [{"item_id": item.id, "qty_kg": 10}], COMPRAS)
    with pytest.raises(DomainError, match="al menos un renglón"):
        procurement.receive(db, po.id, [{"item_id": item.id, "qty_kg": 0, "lot_code": "L-X"}], COMPRAS)
    assert inventory.balance(db, "ESP-001") == 0.0  # nada entró a inventario


def test_recepcion_sin_bodega_se_rechaza(db):
    po = orden(db, kg=50, costo=10, warehouse=None)
    procurement.submit(db, po.id, COMPRAS)
    with pytest.raises(DomainError, match="bodega"):
        procurement.receive(db, po.id, [{"item_id": po.items[0].id, "qty_kg": 10, "lot_code": "L-SB"}], COMPRAS)


# ------------------------------------------------------------------ cancelación
def test_cancelar_exige_motivo_y_no_aplica_a_recibidas(db):
    po = orden(db)
    with pytest.raises(DomainError, match="motivo"):
        procurement.cancel(db, po.id, COMPRAS, "  ")
    assert procurement.cancel(db, po.id, COMPRAS, "El proveedor subió el precio (DEMO)").status == "cancelada"

    otra = orden(db, kg=10, costo=10)
    procurement.submit(db, otra.id, COMPRAS)
    procurement.receive(db, otra.id, [{"item_id": otra.items[0].id, "qty_kg": 10, "lot_code": "L-C1"}], COMPRAS)
    with pytest.raises(DomainError, match="No se puede cancelar"):
        procurement.cancel(db, otra.id, COMPRAS, "ya no la quiero")


# ------------------------------------------------------------------ precios y métricas
def test_historial_de_precios_y_metricas(db):
    otro = procurement.create_supplier(db, {"name": "Importadora del Norte (DEMO)", "origin": "importado"},
                                       COMPRAS)
    a = orden(db, kg=100, costo=40)
    b = procurement.create_order(db, {"supplier_id": otro.id, "warehouse_id": "w-mty"},
                                 [{"product_id": "ESP-001", "qty_kg": 100, "unit_cost_mxn": 60}], COMPRAS)
    cancelada = orden(db, kg=100, costo=999)
    procurement.cancel(db, cancelada.id, COMPRAS, "duplicada (DEMO)")

    h = procurement.price_history(db, "ESP-001")
    assert h["producto"] == "Comino molido" and len(h["compras"]) == 2  # la cancelada no cuenta
    por_proveedor = {p["proveedor"]: p for p in h["por_proveedor"]}
    assert por_proveedor["Especias de Origen (DEMO)"]["ultimo_costo_mxn"] == 40.0
    assert por_proveedor["Importadora del Norte (DEMO)"]["costo_promedio_mxn"] == 60.0

    m = procurement.metrics(db)
    assert m["gasto_por_proveedor"] == {"Importadora del Norte (DEMO)": 6000.0,
                                        "Especias de Origen (DEMO)": 4000.0}
    assert m["costo_promedio_kg"]["Comino molido"] == 50.0
    assert m["por_estado"]["borrador"] == 2 and m["por_estado"]["cancelada"] == 1
    procurement.submit(db, a.id, COMPRAS)
    procurement.submit(db, b.id, COMPRAS)
    m = procurement.metrics(db)
    assert m["pendientes_recibir"] == 2 and m["pendientes_autorizar"] == 0


def test_proveedor_duplicado_y_actualizacion(db):
    with pytest.raises(DomainError, match="Ya existe un proveedor"):
        procurement.create_supplier(db, {"name": "especias de origen (DEMO)"}, COMPRAS)
    s = procurement.update_supplier(db, "sup-1", {"contact_name": "Ana (DEMO)",
                                                  "email": "compras@proveedor.example"}, COMPRAS)
    assert s.contact_name == "Ana (DEMO)" and s.email == "compras@proveedor.example"


# ------------------------------------------------------------------ permisos, CSRF e interfaz
def test_permisos_de_autorizacion_y_escritura(client_for, db):
    po = orden(db, kg=1000, costo=1000)
    procurement.submit(db, po.id, COMPRAS)                  # queda por autorizar
    assert client_for("abastecimiento").post(f"/api/abastecimiento/{po.id}/autorizar").status_code == 403
    assert client_for("admin").post(f"/api/abastecimiento/{po.id}/autorizar").status_code == 200

    lectura = client_for("lectura")
    assert lectura.get("/abastecimiento").status_code == 200
    assert lectura.get("/abastecimiento/proveedores").status_code == 200
    assert lectura.get(f"/abastecimiento/{po.id}").status_code == 200  # detalle sin historial ni botones
    assert lectura.get("/api/abastecimiento").status_code == 200
    nueva = {"supplier_id": "sup-1", "items": [{"product_id": "ESP-001", "qty_kg": 1, "unit_cost_mxn": 1}]}
    assert lectura.post("/api/abastecimiento", json=nueva).status_code == 403
    assert ui_post(lectura, "/abastecimiento", {"supplier_id": "sup-1", "product_id_0": "ESP-001",
                                                "qty_kg_0": 1, "unit_cost_mxn_0": 1}).status_code == 403


def test_post_de_interfaz_sin_csrf_se_rechaza(client_for, db):
    c = client_for("abastecimiento")
    r = c.post("/abastecimiento", data={"supplier_id": "sup-1", "product_id_0": "ESP-001",
                                        "qty_kg_0": 10, "unit_cost_mxn_0": 5})
    assert r.status_code == 403 and "CSRF" in r.text
    assert procurement.orders(db) == []


def test_flujo_completo_por_interfaz(client_for, db):
    c = client_for("admin")
    assert ui_post(c, "/abastecimiento/proveedores", {"name": "Granos del Bajío (DEMO)", "origin": "nacional"},
                   follow_redirects=False).status_code == 303
    r = ui_post(c, "/abastecimiento", {"supplier_id": "sup-1", "warehouse_id": "w-mty",
                                       "expected_date": fecha(7), "product_id_0": "ESP-001",
                                       "qty_kg_0": 500, "unit_cost_mxn_0": 80,
                                       "product_id_1": "GRA-001", "qty_kg_1": 100, "unit_cost_mxn_1": 20},
                 follow_redirects=False)
    assert r.status_code == 303
    po_id = r.headers["location"].rsplit("/", 1)[1]
    db.expire_all()
    po = procurement.get(db, po_id)
    assert len(po.items) == 2 and po.total_mxn == 42000.0

    assert c.get(f"/abastecimiento/{po_id}").status_code == 200
    assert ui_post(c, f"/abastecimiento/{po_id}/enviar", follow_redirects=False).status_code == 303
    db.expire_all()
    assert procurement.get(db, po_id).status == "por_autorizar"
    assert ui_post(c, f"/abastecimiento/{po_id}/autorizar", follow_redirects=False).status_code == 303

    db.expire_all()
    po = procurement.get(db, po_id)
    datos = {"warehouse_id": "w-mty", "supplier_invoice": "A-1234 (DEMO)"}
    for i, it in enumerate(po.items):
        datos |= {f"item_id_{i}": it.id, f"qty_kg_{i}": it.qty_kg, f"lot_code_{i}": f"L-UI-{i}",
                  f"expires_on_{i}": fecha(120)}
    assert ui_post(c, f"/abastecimiento/{po_id}/recibir", datos, follow_redirects=False).status_code == 303
    db.expire_all()
    po = procurement.get(db, po_id)
    assert po.status == "recibida" and po.supplier_invoice == "A-1234 (DEMO)"
    assert inventory.balance(db, "ESP-001", "w-mty") == 500.0
    assert inventory.balance(db, "GRA-001", "w-mty") == 100.0
    assert "OC-0001" in c.get("/abastecimiento").text


def test_flujo_completo_por_api(client_for, db):
    c = client_for("admin")
    r = c.post("/api/abastecimiento", json={"supplier_id": "sup-1", "warehouse_id": "w-mty",
                                            "items": [{"product_id": "ESP-002", "qty_kg": 300,
                                                       "unit_cost_mxn": 120}]})
    assert r.status_code == 201
    po_id = r.json()["orden"]["id"]
    assert c.post(f"/api/abastecimiento/{po_id}/enviar").json()["estado"] == "por_autorizar"
    assert c.post(f"/api/abastecimiento/{po_id}/autorizar").json()["estado"] == "autorizada"
    item_id = c.get("/api/abastecimiento").json()["ordenes"][0]["renglones"][0]["item_id"]
    recibida = c.post(f"/api/abastecimiento/{po_id}/recibir",
                      json={"supplier_invoice": "B-9 (DEMO)",
                            "renglones": [{"item_id": item_id, "qty_kg": 300, "lot_code": "L-API-1",
                                           "expires_on": fecha(90)}]}).json()
    assert recibida["orden"]["estado"] == "recibida" and recibida["orden"]["pendiente_kg"] == 0.0
    assert recibida["existencias"][0] == {"product_id": "ESP-002", "kg": 300.0}
    precios = c.get("/api/abastecimiento/precios/ESP-002").json()
    assert precios["por_proveedor"][0]["ultimo_costo_mxn"] == 120.0


# ------------------------------------------------------------------ bitácora
def test_cada_operacion_deja_rastro_en_la_bitacora(db):
    procurement.create_supplier(db, {"name": "Proveedor bitácora (DEMO)"}, COMPRAS)
    po = orden(db, kg=1000, costo=100)
    procurement.submit(db, po.id, COMPRAS)
    procurement.authorize(db, po.id, "u-admin")
    procurement.receive(db, po.id, [{"item_id": po.items[0].id, "qty_kg": 1000, "lot_code": "L-AUD-1"}],
                        COMPRAS)
    otra = orden(db)
    procurement.cancel(db, otra.id, COMPRAS, "prueba (DEMO)")

    assert acciones(db, "proveedor.") == ["proveedor.alta"]
    assert acciones(db, "compra.") == ["compra.alta", "compra.enviada", "compra.autorizada",
                                       "compra.recepcion", "compra.alta", "compra.cancelada"]
    # la recepción también deja el rastro del lote y de la entrada de inventario
    assert acciones(db, "lote.") == ["lote.alta"] and acciones(db, "inventario.") == ["inventario.entrada"]
    db.expire_all()
    ev = db.scalars(select(AuditEvent).where(AuditEvent.action == "compra.autorizada")).one()
    assert ev.actor_id == "u-admin" and ev.entity_type == "purchase_order" and ev.entity_id == po.id
