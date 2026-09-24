"""Ventas: alta de pedidos, verificación y descuento de existencia, surtido PEPS por caducidad,
folio de factura, permisos y CSRF."""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import Account, AuditEvent, SalesOrder, utcnow
from app.services import crm, inventory, sales
from app.services.common import DomainError
from tests.conftest import ui_post


@pytest.fixture()
def cuenta(db):
    return crm.create_account(db, {"name": "Comedor Industrial del Norte (DEMO)", "is_demo": True}, None)


def _stock(db, kg=1000.0, product_id="ESP-001", warehouse="w-mty", lot_id=None):
    return inventory.move(db, type="entrada", product_id=product_id, warehouse_id=warehouse, qty_kg=kg,
                          lot_id=lot_id, actor_id=None, reason="Carga inicial (DEMO)")


def _lote(db, code, dias, product_id="ESP-001"):
    return inventory.create_lot(db, {"product_id": product_id, "code": code,
                                     "expires_on": (utcnow() + timedelta(days=dias)).date().isoformat()}, None)


def _pedido(db, cuenta, items=None, **extra):
    data = {"account_id": cuenta.id, "warehouse_id": "w-mty",
            "promised_date": (utcnow() + timedelta(days=3)).date().isoformat(), **extra}
    return sales.create_order(db, data, items or [{"product_id": "ESP-001", "qty_kg": 300,
                                                   "unit_price_mxn": 90}], "u-ventas")


# ------------------------------------------------------------------ alta
def test_alta_folio_por_conteo_y_conversion_de_unidades(db, cuenta):
    o = _pedido(db, cuenta, [{"product_id": "ESP-001", "qty": 4, "unit": "saco", "unit_price_mxn": 80}])
    assert o.folio == "PED-0001" and o.status == "borrador"
    assert o.total_kg == 100.0 and o.total_mxn == 8000.0  # 4 sacos × 25 kg
    assert _pedido(db, cuenta).folio == "PED-0002"


@pytest.mark.parametrize("cambio,vacio,msg", [
    ({"account_id": ""}, False, "Cuenta"),
    ({"warehouse_id": ""}, False, "Bodega"),
    ({"promised_date": ""}, False, "fecha prometida"),
    ({}, True, "al menos un renglón"),
])
def test_alta_valida_lo_indispensable(db, cuenta, cambio, vacio, msg):
    data = {"account_id": cuenta.id, "warehouse_id": "w-mty",
            "promised_date": (utcnow() + timedelta(days=2)).date().isoformat(), **cambio}
    items = [] if vacio else [{"product_id": "ESP-001", "qty_kg": 100}]
    with pytest.raises(DomainError, match=msg):
        sales.create_order(db, data, items, "u-ventas")


# ------------------------------------------------------------------ existencia
def test_entregar_descuenta_los_kilos_vendidos_y_liga_el_movimiento(db, cuenta):
    _stock(db, 1000)
    o = _pedido(db, cuenta)
    sales.confirm(db, o.id, "u-ventas")
    assert o.status == "confirmado"
    assert inventory.balance(db, "ESP-001", "w-mty") == 1000  # confirmar NO descuenta
    sales.deliver(db, o.id, "u-ventas")
    assert inventory.balance(db, "ESP-001", "w-mty") == 700
    mvs = sales.movements_of(db, o.id)
    assert len(mvs) == 1 and mvs[0].qty_kg == -300 and mvs[0].type == "salida"
    assert mvs[0].ref_type == "pedido" and mvs[0].ref_id == o.id
    assert o.status == "entregado" and o.delivered_at is not None
    assert db.get(Account, cuenta.id).lifecycle == "cliente_activo"  # ya recibió mercancía


def test_confirmar_sin_existencia_falla_y_no_mueve_nada(db, cuenta):
    _stock(db, 100)
    o = _pedido(db, cuenta)  # pide 300 kg
    with pytest.raises(DomainError, match="existencia suficiente") as e:
        sales.confirm(db, o.id, "u-ventas")
    assert e.value.status_code == 422
    assert inventory.balance(db, "ESP-001", "w-mty") == 100 and o.status == "borrador"


def test_entregar_sin_existencia_falla_y_deja_el_inventario_igual(db, cuenta):
    _stock(db, 1000)
    o = _pedido(db, cuenta)
    sales.confirm(db, o.id, "u-ventas")
    inventory.move(db, type="salida", product_id="ESP-001", warehouse_id="w-mty", qty_kg=-900,
                   actor_id=None, reason="Se surtió otro pedido primero (DEMO)")
    with pytest.raises(DomainError, match="existencia suficiente"):
        sales.deliver(db, o.id, "u-ventas")
    assert inventory.balance(db, "ESP-001", "w-mty") == 100
    assert db.get(SalesOrder, o.id).status == "confirmado"


def test_api_entregar_sin_existencia_devuelve_422(client_for, db, cuenta):
    _stock(db, 1000)
    o = _pedido(db, cuenta)
    sales.confirm(db, o.id, "u-ventas")
    inventory.move(db, type="salida", product_id="ESP-001", warehouse_id="w-mty", qty_kg=-900,
                   actor_id=None, reason="Otra salida (DEMO)")
    r = client_for("ventas").post(f"/api/ventas/{o.id}/entregar")
    assert r.status_code == 422 and "existencia" in r.json()["detail"]
    assert inventory.balance(db, "ESP-001", "w-mty") == 100


def test_existencia_de_otra_bodega_no_cuenta(db, cuenta):
    _stock(db, 1000, warehouse="w-tmp")
    o = _pedido(db, cuenta)
    with pytest.raises(DomainError, match="existencia suficiente"):
        sales.confirm(db, o.id, "u-ventas")


# ------------------------------------------------------------------ surtido PEPS por caducidad
def test_sin_lote_surte_primero_el_que_caduca_antes_y_parte_el_renglon(db, cuenta):
    viejo, nuevo = _lote(db, "L-VIEJO", 20), _lote(db, "L-NUEVO", 300)
    _stock(db, 100, lot_id=viejo.id)
    _stock(db, 500, lot_id=nuevo.id)
    o = _pedido(db, cuenta, [{"product_id": "ESP-001", "qty_kg": 250, "unit_price_mxn": 95}])
    sales.confirm(db, o.id, "u-ventas")
    sales.deliver(db, o.id, "u-ventas")
    mvs = sales.movements_of(db, o.id)
    assert [(m.lot_id, m.qty_kg) for m in mvs] == [(viejo.id, -100.0), (nuevo.id, -150.0)]
    assert inventory.balance(db, lot_id=viejo.id) == 0 and inventory.balance(db, lot_id=nuevo.id) == 350


def test_con_lote_indicado_se_respeta_ese_lote(db, cuenta):
    viejo, nuevo = _lote(db, "L-VIEJO", 20), _lote(db, "L-NUEVO", 300)
    _stock(db, 200, lot_id=viejo.id)
    _stock(db, 200, lot_id=nuevo.id)
    o = _pedido(db, cuenta, [{"product_id": "ESP-001", "qty_kg": 150, "lot_id": nuevo.id}])
    sales.confirm(db, o.id, "u-ventas")
    sales.deliver(db, o.id, "u-ventas")
    assert inventory.balance(db, lot_id=nuevo.id) == 50 and inventory.balance(db, lot_id=viejo.id) == 200


def test_lote_de_otro_producto_no_se_acepta(db, cuenta):
    otro = inventory.create_lot(db, {"product_id": "GRA-001", "code": "L-ARROZ"}, None)
    with pytest.raises(DomainError, match="no pertenece"):
        _pedido(db, cuenta, [{"product_id": "ESP-001", "qty_kg": 10, "lot_id": otro.id}])


# ------------------------------------------------------------------ cancelación y factura
def test_pedido_entregado_no_se_puede_cancelar(db, cuenta):
    _stock(db, 500)
    o = _pedido(db, cuenta)
    sales.confirm(db, o.id, "u-ventas")
    sales.deliver(db, o.id, "u-ventas")
    with pytest.raises(DomainError, match="entregado"):
        sales.cancel(db, o.id, "u-ventas", "el cliente se arrepintió")
    assert db.get(SalesOrder, o.id).status == "entregado"


def test_cancelar_antes_de_entregar_exige_motivo(db, cuenta):
    o = _pedido(db, cuenta)
    with pytest.raises(DomainError, match="motivo"):
        sales.cancel(db, o.id, "u-ventas", "  ")
    sales.cancel(db, o.id, "u-ventas", "el cliente pospuso la compra")
    assert o.status == "cancelado" and "pospuso" in o.notes


def test_folio_de_factura_queda_en_la_bitacora(db, cuenta):
    _stock(db, 500)
    o = _pedido(db, cuenta)
    sales.confirm(db, o.id, "u-ventas")
    sales.deliver(db, o.id, "u-ventas")
    sales.set_invoice(db, o.id, "A-12345", "u-ventas")
    ev = db.scalar(select(AuditEvent).where(AuditEvent.action == "pedido.factura",
                                            AuditEvent.entity_id == o.id))
    assert ev is not None and "A-12345" in ev.summary
    assert ev.after["invoice_folio"] == "A-12345" and ev.before["invoice_folio"] is None
    assert ev.actor_id == "u-ventas"
    with pytest.raises(DomainError, match="folio"):
        sales.set_invoice(db, o.id, "", "u-ventas")


# ------------------------------------------------------------------ consultas
def test_for_account_y_metricas(db, cuenta):
    _stock(db, 1000)
    o = _pedido(db, cuenta)
    sales.confirm(db, o.id, "u-ventas")
    sales.deliver(db, o.id, "u-ventas")
    _pedido(db, cuenta)  # queda en borrador
    assert [x.folio for x in sales.for_account(db, cuenta.id)] == ["PED-0002", "PED-0001"]
    m = sales.metrics(db)
    assert m["por_estado"]["entregado"] == 1 and m["por_estado"]["borrador"] == 1
    assert m["kg_total"] == 600 and m["top_clientes"][0]["nombre"] == cuenta.name
    assert m["top_productos"][0]["nombre"] == "Comino molido"
    assert len(m["por_mes"]) == 6 and m["por_mes"][-1]["kg"] == 600


# ------------------------------------------------------------------ interfaz y API
def test_alta_y_flujo_por_la_interfaz(client_for, db, cuenta):
    _stock(db, 1000)
    c = client_for("ventas")
    assert c.get("/ventas").status_code == 200
    r = ui_post(c, "/ventas", {"account_id": cuenta.id, "warehouse_id": "w-mty",
                               "promised_date": (utcnow() + timedelta(days=5)).date().isoformat(),
                               "product_id_0": "ESP-001", "qty_0": "2", "unit_0": "saco",
                               "unit_price_mxn_0": "100"}, follow_redirects=False)
    assert r.status_code == 303
    o = db.scalar(select(SalesOrder))
    assert o.total_kg == 50.0
    assert c.get(f"/ventas/{o.id}").status_code == 200
    assert ui_post(c, f"/ventas/{o.id}/confirmar", follow_redirects=False).status_code == 303
    assert ui_post(c, f"/ventas/{o.id}/entregar", follow_redirects=False).status_code == 303
    assert ui_post(c, f"/ventas/{o.id}/factura", {"invoice_folio": "B-77"}, follow_redirects=False).status_code == 303
    db.expire_all()
    assert db.get(SalesOrder, o.id).status == "entregado"
    assert inventory.balance(db, "ESP-001", "w-mty") == 950
    detalle = c.get(f"/ventas/{o.id}")  # la ficha ya muestra la salida de inventario y la factura
    assert detalle.status_code == 200 and "B-77" in detalle.text and "Entregado" in detalle.text


def test_api_alta_entrega_y_metricas(client_for, db, cuenta):
    _stock(db, 1000)
    c = client_for("ventas")
    r = c.post("/api/ventas", json={"account_id": cuenta.id, "warehouse_id": "w-mty",
                                    "promised_date": (utcnow() + timedelta(days=4)).date().isoformat(),
                                    "items": [{"product_id": "ESP-001", "qty": 4, "unit": "saco",
                                               "unit_price_mxn": 80}]})
    assert r.status_code == 201 and r.json()["total_kg"] == 100.0
    oid = r.json()["order"]["id"]
    assert ui_post(c, f"/ventas/{oid}/confirmar", follow_redirects=False).status_code == 303
    entrega = c.post(f"/api/ventas/{oid}/entregar").json()
    assert entrega["order"]["status"] == "entregado" and entrega["movimientos"][0]["qty_kg"] == -100.0
    assert [o["folio"] for o in c.get("/api/ventas?status=entregado").json()] == ["PED-0001"]
    m = c.get("/api/ventas/metricas").json()
    assert m["por_estado"]["entregado"] == 1 and m["pendientes"] == []


# ------------------------------------------------------------------ permisos
def test_rol_lectura_no_escribe_y_la_interfaz_exige_csrf(client_for, db, cuenta):
    _stock(db, 500)
    o = _pedido(db, cuenta)
    lectura = client_for("lectura")
    assert lectura.get("/ventas").status_code == 200 and lectura.get(f"/ventas/{o.id}").status_code == 200
    assert lectura.post("/api/ventas", json={"account_id": cuenta.id}).status_code == 403
    assert lectura.post(f"/api/ventas/{o.id}/entregar").status_code == 403
    assert ui_post(lectura, f"/ventas/{o.id}/confirmar").status_code == 403
    ventas = client_for("ventas")
    assert ventas.post(f"/ventas/{o.id}/confirmar").status_code == 403           # sin csrf_token
    assert ventas.post(f"/ventas/{o.id}/confirmar", data={"csrf_token": "x"}).status_code == 403
    db.expire_all()
    assert db.get(SalesOrder, o.id).status == "borrador"
    assert ui_post(ventas, f"/ventas/{o.id}/confirmar", follow_redirects=False).status_code == 303
