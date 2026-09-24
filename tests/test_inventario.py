"""Inventario: captura en la unidad del producto, existencia nunca negativa, traspasos, alertas,
permisos y rastro en la bitácora."""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import AuditEvent, StockMovement, utcnow
from app.services import inventory
from app.services.common import DomainError
from tests.conftest import ui_post

ALMACEN = "u-almacen"


def entrada(db, qty=10, unit="saco", product="ESP-001", warehouse="w-mty", lot_id=None):
    return inventory.register(db, {"type": "entrada", "product_id": product, "warehouse_id": warehouse,
                                   "qty": qty, "unit": unit, "lot_id": lot_id}, ALMACEN)


def acciones(db, prefijo: str) -> list[str]:
    db.expire_all()
    return [e.action for e in db.scalars(select(AuditEvent).order_by(AuditEvent.seq))
            if e.action.startswith(prefijo)]


def fecha(dias: int) -> str:
    return (utcnow() + timedelta(days=dias)).date().isoformat()


# ------------------------------------------------------------------ conversión a kilos
def test_entrada_en_sacos_se_guarda_en_kilos(db):
    """El almacenista captura 10 sacos; el sistema guarda 250 kg (25 kg por saco)."""
    mv = entrada(db, qty=10, unit="saco")
    assert mv.qty_kg == 250.0 and mv.type == "entrada"
    assert inventory.balance(db, "ESP-001", "w-mty") == 250.0
    fila = inventory.stock_rows(db, "ESP-001")[0]
    assert fila["kg"] == 250.0 and fila["warehouse"].code == "MTY"
    assert inventory.by_product(db)[0]["kg"] >= 0


def test_captura_en_kilos_y_en_tarimas(db):
    entrada(db, qty=40, unit="kg", product="ESP-002")
    assert inventory.balance(db, "ESP-002") == 40.0
    entrada(db, qty=2, unit="tarima", product="ESP-002")  # usa kg_per_unit del producto (25)
    assert inventory.balance(db, "ESP-002") == 90.0


# ------------------------------------------------------------------ existencia nunca negativa
def test_salida_mayor_que_la_existencia_se_rechaza(db):
    entrada(db, qty=2)  # 50 kg
    with pytest.raises(DomainError) as e:
        inventory.register(db, {"type": "salida", "product_id": "ESP-001", "warehouse_id": "w-mty",
                                "qty": 5, "unit": "saco"}, ALMACEN)
    assert "No hay existencia suficiente" in e.value.message and "50" in e.value.message
    assert inventory.balance(db, "ESP-001", "w-mty") == 50.0


def test_api_salida_mayor_devuelve_422_y_no_deja_negativo(client_for, db):
    c = client_for("almacen")
    base = {"product_id": "ESP-001", "warehouse_id": "w-mty", "unit": "saco"}
    assert c.post("/api/inventario/movimientos", json={**base, "type": "entrada", "qty": 2}).status_code == 201
    r = c.post("/api/inventario/movimientos", json={**base, "type": "salida", "qty": 5})
    assert r.status_code == 422 and "No hay existencia suficiente" in r.json()["detail"]
    assert inventory.balance(db, "ESP-001", "w-mty") == 50.0
    assert all(inventory.balance(db, m.product_id, m.warehouse_id) >= 0
               for m in db.scalars(select(StockMovement)))


def test_ajuste_sin_motivo_se_rechaza(db):
    entrada(db, qty=4)
    with pytest.raises(DomainError, match="motivo"):
        inventory.register(db, {"type": "ajuste", "product_id": "ESP-001", "warehouse_id": "w-mty",
                                "qty": -1, "unit": "saco"}, ALMACEN)
    mv = inventory.register(db, {"type": "ajuste", "product_id": "ESP-001", "warehouse_id": "w-mty",
                                 "qty": 1, "unit": "saco", "reason": "Conteo físico (DEMO)"}, ALMACEN)
    assert mv.reason == "Conteo físico (DEMO)"


# ------------------------------------------------------------------ traspasos
def test_traspaso_mueve_kilos_entre_bodegas_sin_alterar_el_total(db):
    entrada(db, qty=8)  # 200 kg en MTY
    total = inventory.balance(db, "ESP-001")
    movs = inventory.transfer(db, {"product_id": "ESP-001", "from_warehouse_id": "w-mty",
                                   "to_warehouse_id": "w-tmp", "qty": 3, "unit": "saco"}, ALMACEN)
    assert [m.qty_kg for m in movs] == [-75.0, 75.0]
    assert inventory.balance(db, "ESP-001", "w-mty") == 125.0
    assert inventory.balance(db, "ESP-001", "w-tmp") == 75.0
    assert inventory.balance(db, "ESP-001") == total
    assert movs[0].ref_id == movs[1].ref_id  # misma referencia: el par se puede rastrear junto


def test_traspaso_a_la_misma_bodega_o_sin_existencia_se_rechaza(db):
    entrada(db, qty=1)
    with pytest.raises(DomainError, match="distinta"):
        inventory.transfer(db, {"product_id": "ESP-001", "from_warehouse_id": "w-mty",
                                "to_warehouse_id": "w-mty", "qty": 1, "unit": "saco"}, ALMACEN)
    with pytest.raises(DomainError, match="No hay existencia suficiente"):
        inventory.transfer(db, {"product_id": "ESP-001", "from_warehouse_id": "w-tmp",
                                "to_warehouse_id": "w-mty", "qty": 1, "unit": "saco"}, ALMACEN)


# ------------------------------------------------------------------ alertas
def test_alerta_de_bajo_minimo(db):
    entrada(db, qty=2)  # 50 kg contra un mínimo de 100 kg
    bajos = {r["product"].id: r for r in inventory.low_stock(db)}
    assert "ESP-001" in bajos and bajos["ESP-001"]["kg"] == 50.0 and bajos["ESP-001"]["min_kg"] == 100.0
    entrada(db, qty=4)  # 150 kg: ya está arriba del mínimo
    assert "ESP-001" not in {r["product"].id for r in inventory.low_stock(db)}
    assert inventory.metrics(db)["bajo_minimo"] == len(inventory.low_stock(db))


def test_lote_por_caducar_aparece_con_saldo_y_no_cuando_ya_salio_todo(db):
    cerca = inventory.create_lot(db, {"product_id": "ESP-001", "code": "L-DEMO-CERCA",
                                      "expires_on": fecha(10)}, ALMACEN)
    lejos = inventory.create_lot(db, {"product_id": "ESP-001", "code": "L-DEMO-LEJOS",
                                      "expires_on": fecha(400)}, ALMACEN)
    entrada(db, qty=4, lot_id=cerca.id)
    entrada(db, qty=4, lot_id=lejos.id)
    avisos = {r["lot"].id: r["kg"] for r in inventory.expiring_lots(db)}
    assert avisos == {cerca.id: 100.0}  # el lote lejano no alerta todavía

    inventory.register(db, {"type": "salida", "product_id": "ESP-001", "warehouse_id": "w-mty",
                            "qty": 4, "unit": "saco", "lot_id": cerca.id}, ALMACEN)
    assert inventory.expiring_lots(db) == []  # sin saldo ya no es un aviso útil


def test_lote_de_otro_producto_se_rechaza(db):
    lot = inventory.create_lot(db, {"product_id": "ESP-001", "code": "L-DEMO-X"}, ALMACEN)
    with pytest.raises(DomainError, match="no pertenece"):
        entrada(db, product="ESP-002", lot_id=lot.id)


# ------------------------------------------------------------------ permisos y CSRF
def test_rol_lectura_no_escribe_pero_consulta(client_for, db):
    c = client_for("lectura")
    assert c.get("/inventario").status_code == 200
    assert c.get("/inventario/movimientos").status_code == 200  # sin los formularios de captura
    assert "Registrar movimiento" not in c.get("/inventario/movimientos").text
    assert c.get("/api/inventario/existencias").status_code == 200
    body = {"type": "entrada", "product_id": "ESP-001", "warehouse_id": "w-mty", "qty": 1, "unit": "saco"}
    assert c.post("/api/inventario/movimientos", json=body).status_code == 403
    assert ui_post(c, "/inventario/movimientos", body).status_code == 403
    assert ui_post(c, "/inventario/bodegas", {"code": "X", "name": "X"}).status_code == 403
    assert inventory.balance(db, "ESP-001") == 0.0


def test_post_de_interfaz_sin_csrf_se_rechaza(client_for, db):
    c = client_for("almacen")
    r = c.post("/inventario/movimientos", data={"type": "entrada", "product_id": "ESP-001",
                                                "warehouse_id": "w-mty", "qty": 1, "unit": "saco"})
    assert r.status_code == 403 and "CSRF" in r.text
    assert inventory.balance(db, "ESP-001") == 0.0


# ------------------------------------------------------------------ pantallas y API
def test_pantallas_del_modulo_responden(client_for, db):
    entrada(db, qty=2)
    c = client_for("almacen")
    for url in ["/inventario", "/inventario/movimientos", "/inventario/lotes", "/inventario/productos",
                "/inventario/bodegas"]:
        r = c.get(url)
        assert r.status_code == 200, url
    assert "Comino molido" in c.get("/inventario").text
    assert "Bodega Guadalupe" in c.get("/inventario/bodegas").text


def test_alta_por_interfaz_de_bodega_producto_lote_y_movimiento(client_for, db):
    c = client_for("almacen")
    assert ui_post(c, "/inventario/bodegas", {"code": "sal", "name": "Bodega salida (DEMO)"},
                   follow_redirects=False).status_code == 303
    assert ui_post(c, "/inventario/productos", {"sku": "esp-900", "name": "Orégano (DEMO)", "unit": "caja",
                                                "kg_per_unit": 10, "min_stock_kg": 50, "shelf_life_days": 365},
                   follow_redirects=False).status_code == 303
    assert ui_post(c, "/inventario/lotes", {"product_id": "ESP-001", "code": "l-demo-ui",
                                            "expires_on": fecha(90)}, follow_redirects=False).status_code == 303
    assert ui_post(c, "/inventario/movimientos", {"type": "entrada", "product_id": "ESP-001",
                                                  "warehouse_id": "w-mty", "qty": 3, "unit": "saco"},
                   follow_redirects=False).status_code == 303
    db.expire_all()
    assert inventory.balance(db, "ESP-001", "w-mty") == 75.0
    productos = {p["product"].sku: p["product"] for p in inventory.by_product(db)}
    assert productos["ESP-900"].unit == "caja" and productos["ESP-900"].kg_per_unit == 10.0


def test_traspaso_por_interfaz_y_api(client_for, db):
    entrada(db, qty=4)
    c = client_for("almacen")
    assert ui_post(c, "/inventario/traspasos", {"product_id": "ESP-001", "from_warehouse_id": "w-mty",
                                                "to_warehouse_id": "w-tmp", "qty": 1, "unit": "saco"},
                   follow_redirects=False).status_code == 303
    r = c.post("/api/inventario/traspasos", json={"product_id": "ESP-001", "from_warehouse_id": "w-mty",
                                                  "to_warehouse_id": "w-tmp", "qty": 25, "unit": "kg"})
    assert r.status_code == 201 and len(r.json()["movimientos"]) == 2
    assert inventory.balance(db, "ESP-001", "w-tmp") == 50.0
    assert inventory.balance(db, "ESP-001") == 100.0


def test_api_existencias_y_alertas(client_for, db):
    lot = inventory.create_lot(db, {"product_id": "ESP-001", "code": "L-API", "expires_on": fecha(5)}, ALMACEN)
    entrada(db, qty=2, lot_id=lot.id)
    c = client_for("almacen")
    data = c.get("/api/inventario/existencias?product_id=ESP-001").json()
    assert data["existencias"] == [{"product_id": "ESP-001", "sku": "ESP-001", "producto": "Comino molido",
                                    "lot_id": lot.id, "lote": "L-API", "warehouse_id": "w-mty",
                                    "bodega": "MTY", "kg": 50.0, "caduca": fecha(5)}]
    assert data["metricas"]["kg_total"] == 50.0
    alertas = c.get("/api/inventario/alertas").json()
    assert {a["sku"] for a in alertas["bajo_minimo"]} >= {"ESP-001"}
    assert alertas["por_caducar"][0]["lote"] == "L-API" and alertas["por_caducar"][0]["kg"] == 50.0


# ------------------------------------------------------------------ bitácora
def test_cada_operacion_deja_rastro_en_la_bitacora(db):
    inventory.create_warehouse(db, {"code": "aud", "name": "Bodega auditoría (DEMO)"}, ALMACEN)
    inventory.create_product(db, {"sku": "aud-1", "name": "Producto auditoría (DEMO)", "unit": "kg"}, ALMACEN)
    inventory.create_lot(db, {"product_id": "ESP-001", "code": "L-AUD"}, ALMACEN)
    entrada(db, qty=4)
    inventory.transfer(db, {"product_id": "ESP-001", "from_warehouse_id": "w-mty",
                            "to_warehouse_id": "w-tmp", "qty": 1, "unit": "saco"}, ALMACEN)
    inventory.update_product(db, "ESP-001", {"min_stock_kg": 250}, ALMACEN)
    assert acciones(db, "bodega.") == ["bodega.alta"]
    assert acciones(db, "producto.") == ["producto.alta", "producto.cambio"]
    assert acciones(db, "lote.") == ["lote.alta"]
    assert acciones(db, "inventario.") == ["inventario.entrada", "inventario.traspaso", "inventario.traspaso"]
    db.expire_all()
    ev = db.scalars(select(AuditEvent).where(AuditEvent.action == "inventario.entrada")).one()
    assert ev.actor_id == ALMACEN and ev.after["kg"] == 100.0 and ev.after["existencia_resultante"] == 100.0
