"""Mantenimiento: activos, frecuencias por días/kilómetros/horas, órdenes, vencimientos y permisos."""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import Asset, AuditEvent, MaintenancePlan, WorkOrder, utcnow
from app.services import maintenance
from app.services.common import DomainError
from tests.conftest import ui_post

ACTOR = "u-mantenimiento"


def _camion(db, km=10000.0, **extra):
    return maintenance.create_asset(db, {"code": extra.pop("code", "CAM-01"), "name": "Camión de reparto (DEMO)",
                                         "type": "camion", "identifier": "ABC-123-XY",
                                         "odometer_km": km, **extra}, ACTOR)


def _fecha(dias):
    return (utcnow() + timedelta(days=dias)).date().isoformat()


# ------------------------------------------------------------------ activos
def test_alta_asignacion_y_estado(db):
    a = _camion(db)
    assert a.code == "CAM-01" and a.status == "activo" and a.odometer_km == 10000
    with pytest.raises(DomainError, match="Ya existe"):
        _camion(db)
    maintenance.assign(db, a.id, ACTOR, user_id="u-ventas")
    assert a.assigned_user_id == "u-ventas"
    with pytest.raises(DomainError, match="a quién"):
        maintenance.assign(db, a.id, ACTOR)
    maintenance.set_status(db, a.id, "reparacion", ACTOR)
    assert a.status == "reparacion"
    with pytest.raises(DomainError, match="Estado de activo"):
        maintenance.set_status(db, a.id, "chatarra", ACTOR)


def test_el_odometro_solo_sube(db):
    a = _camion(db, km=10000)
    maintenance.update_asset(db, a.id, {"odometer_km": 12500}, ACTOR)
    assert a.odometer_km == 12500
    with pytest.raises(DomainError, match="no puede bajar"):
        maintenance.update_asset(db, a.id, {"odometer_km": 9000}, ACTOR)
    assert db.get(Asset, a.id).odometer_km == 12500


# ------------------------------------------------------------------ planes ("asignar frecuencia")
def test_plan_necesita_al_menos_una_frecuencia(db):
    a = _camion(db)
    with pytest.raises(DomainError, match="al menos una frecuencia"):
        maintenance.create_plan(db, a.id, {"name": "Revisión general"}, ACTOR)
    with pytest.raises(DomainError, match="nombre"):
        maintenance.create_plan(db, a.id, {"freq_days": 30}, ACTOR)


def test_plan_calcula_el_primer_vencimiento_desde_la_lectura_actual(db):
    a = _camion(db, km=10000, hours_used=800)
    p = maintenance.create_plan(db, a.id, {"name": "Servicio mayor", "freq_days": 180, "freq_km": 10000,
                                           "freq_hours": 500}, ACTOR)
    assert p.next_due_km == 20000 and p.next_due_hours == 1300
    assert (p.next_due_on.date() - utcnow().date()).days == 180


def test_plan_por_kilometros_se_recorre_al_cerrar_la_orden(db):
    a = _camion(db, km=10000)
    p = maintenance.create_plan(db, a.id, {"name": "Cambio de aceite", "freq_km": 10000}, ACTOR)
    assert p.next_due_km == 20000
    wo = maintenance.create_work_order(db, {"asset_id": a.id, "plan_id": p.id, "kind": "preventivo",
                                            "description": "Aceite y filtros"}, ACTOR)
    assert wo.folio == "OM-0001" and wo.status == "abierta"
    maintenance.close_work_order(db, wo.id, {"cost_mxn": 3500, "odometer_km": 20500,
                                             "done_on": _fecha(0)}, ACTOR)
    assert wo.status == "cerrada" and wo.cost_mxn == 3500
    assert a.odometer_km == 20500              # el odómetro del activo sube con la lectura de la orden
    assert p.last_done_km == 20500 and p.next_due_km == 30500  # el siguiente vencimiento se recorre
    assert maintenance.plan_state(p, a)["estado"] is None
    with pytest.raises(DomainError, match="ya está cerrada"):
        maintenance.close_work_order(db, wo.id, {}, ACTOR)


def test_cerrar_no_baja_el_odometro_del_activo(db):
    a = _camion(db, km=30000)
    wo = maintenance.create_work_order(db, {"asset_id": a.id, "description": "Frenos", "kind": "correctivo"}, ACTOR)
    maintenance.close_work_order(db, wo.id, {"odometer_km": 100}, ACTOR)  # error de dedo del taller
    assert a.odometer_km == 30000


def test_orden_externa_exige_nombre_del_proveedor(db):
    a = _camion(db)
    with pytest.raises(DomainError, match="proveedor externo"):
        maintenance.create_work_order(db, {"asset_id": a.id, "description": "Alineación",
                                           "provider": "externo"}, ACTOR)
    wo = maintenance.create_work_order(db, {"asset_id": a.id, "description": "Alineación",
                                            "provider": "externo", "provider_name": "Taller Díaz (DEMO)"}, ACTOR)
    assert wo.provider_name == "Taller Díaz (DEMO)"


# ------------------------------------------------------------------ vencimientos
def test_due_plans_detecta_vencido_por_fecha_y_por_kilometraje(db):
    a = _camion(db, km=10000)
    por_fecha = maintenance.create_plan(db, a.id, {"name": "Verificación", "freq_days": 30,
                                                   "last_done_on": _fecha(-90)}, ACTOR)
    por_km = maintenance.create_plan(db, a.id, {"name": "Afinación", "freq_km": 5000,
                                                "last_done_km": 1000}, ACTOR)
    al_corriente = maintenance.create_plan(db, a.id, {"name": "Servicio mayor", "freq_km": 50000}, ACTOR)
    pendientes = maintenance.due_plans(db)
    ids = {p["plan"].id: p for p in pendientes}
    assert al_corriente.id not in ids
    assert ids[por_fecha.id]["estado"] == "vencido" and "fecha" in " ".join(ids[por_fecha.id]["razones"])
    assert ids[por_km.id]["estado"] == "vencido" and "kilometraje" in " ".join(ids[por_km.id]["razones"])
    assert ids[por_km.id]["km_faltantes"] == -4000


def test_due_plans_avisa_de_los_proximos_y_omite_los_activos_de_baja(db):
    a = _camion(db, km=10000)
    proximo = maintenance.create_plan(db, a.id, {"name": "Llantas", "freq_km": 300}, ACTOR)  # faltan 300 km
    assert maintenance.due_plans(db)[0]["plan"].id == proximo.id
    assert maintenance.due_plans(db)[0]["estado"] == "proximo"
    maintenance.set_status(db, a.id, "baja", ACTOR)
    assert maintenance.due_plans(db) == []


def test_metricas(db):
    a = _camion(db, km=10000)
    b = _camion(db, code="CLI-01", km=None, type="clima")
    p = maintenance.create_plan(db, a.id, {"name": "Aceite", "freq_days": 30, "last_done_on": _fecha(-60)}, ACTOR)
    wo = maintenance.create_work_order(db, {"asset_id": a.id, "plan_id": p.id, "description": "Aceite"}, ACTOR)
    maintenance.create_work_order(db, {"asset_id": b.id, "description": "Limpieza de filtros"}, ACTOR)
    maintenance.close_work_order(db, wo.id, {"cost_mxn": 2500, "odometer_km": 10500}, ACTOR)
    m = maintenance.metrics(db)
    assert m["activos"] == 2 and m["por_tipo"]["Camión"] == 1 and m["por_tipo"]["Clima"] == 1
    assert m["ordenes_abiertas"] == 1 and m["costo_periodo_mxn"] == 2500
    assert m["costo_por_activo"][0]["mxn"] == 2500
    assert m["vencidos"] + m["proximos"] == 0  # al cerrar la orden el plan quedó al corriente


# ------------------------------------------------------------------ interfaz y API
def test_ficha_360_y_captura_de_kilometraje_por_la_interfaz(client_for, db):
    a = _camion(db, km=10000)
    maintenance.create_plan(db, a.id, {"name": "Cambio de aceite", "freq_km": 10000}, ACTOR)
    c = client_for("mantenimiento")
    assert c.get("/mantenimiento").status_code == 200
    ficha = c.get(f"/mantenimiento/activos/{a.id}")
    assert ficha.status_code == 200 and "Cambio de aceite" in ficha.text and "ABC-123-XY" in ficha.text
    assert ui_post(c, f"/mantenimiento/activos/{a.id}/odometro", {"odometer_km": "15000"},
                   follow_redirects=False).status_code == 303
    db.expire_all()
    assert db.get(Asset, a.id).odometer_km == 15000
    assert c.get("/mantenimiento/ordenes").status_code == 200


def test_alta_plan_y_orden_por_la_interfaz(client_for, db):
    c = client_for("mantenimiento")
    r = ui_post(c, "/mantenimiento/activos", {"code": "MON-01", "name": "Montacargas (DEMO)",
                                              "type": "equipo", "hours_used": "1200"}, follow_redirects=False)
    assert r.status_code == 303
    a = db.scalar(select(Asset).where(Asset.code == "MON-01"))
    assert ui_post(c, f"/mantenimiento/activos/{a.id}/planes",
                   {"name": "Servicio de 250 h", "freq_hours": "250"}, follow_redirects=False).status_code == 303
    plan = db.scalar(select(MaintenancePlan).where(MaintenancePlan.asset_id == a.id))
    assert plan.next_due_hours == 1450
    assert ui_post(c, "/mantenimiento/ordenes", {"asset_id": a.id, "plan_id": plan.id,
                                                 "description": "Servicio programado"},
                   follow_redirects=False).status_code == 303
    wo = db.scalar(select(WorkOrder).where(WorkOrder.asset_id == a.id))
    assert ui_post(c, f"/mantenimiento/ordenes/{wo.id}/cerrar",
                   {"cost_mxn": "1800", "hours_used": "1260"}, follow_redirects=False).status_code == 303
    db.expire_all()
    assert db.get(WorkOrder, wo.id).status == "cerrada"
    assert db.get(MaintenancePlan, plan.id).next_due_hours == 1510
    assert db.scalar(select(AuditEvent).where(AuditEvent.action == "orden_mantenimiento.cierre")) is not None
    ficha = c.get(f"/mantenimiento/activos/{a.id}")  # la ficha ya muestra la orden cerrada y su costo
    assert ficha.status_code == 200 and "Cerrada" in ficha.text and "1,800.00" in ficha.text


def test_api_activos_pendientes_y_cierre(client_for, db):
    c = client_for("mantenimiento")
    r = c.post("/api/mantenimiento/activos", json={"code": "CAM-99", "name": "Camión (DEMO)",
                                                   "type": "camion", "odometer_km": 5000})
    assert r.status_code == 201
    a = db.scalar(select(Asset).where(Asset.code == "CAM-99"))
    maintenance.create_plan(db, a.id, {"name": "Afinación", "freq_km": 1000, "last_done_km": 100}, ACTOR)
    pendientes = c.get("/api/mantenimiento/pendientes").json()
    assert pendientes["vencidos"][0]["activo"] == "CAM-99"
    assert pendientes["metricas"]["vencidos"] == 1
    assert [x["code"] for x in c.get("/api/mantenimiento/activos?type=camion").json()] == ["CAM-99"]
    wo = maintenance.create_work_order(db, {"asset_id": a.id, "description": "Afinación mayor"}, ACTOR)
    cierre = c.post(f"/api/mantenimiento/ordenes/{wo.id}/cerrar",
                    json={"cost_mxn": 4200, "odometer_km": 5200})
    assert cierre.status_code == 200 and cierre.json()["orden"]["status"] == "cerrada"
    assert cierre.json()["activo"]["odometer_km"] == 5200


# ------------------------------------------------------------------ permisos
def test_rol_lectura_no_escribe_y_la_interfaz_exige_csrf(client_for, db):
    a = _camion(db)
    lectura = client_for("lectura")
    assert lectura.get("/mantenimiento").status_code == 200
    assert lectura.get(f"/mantenimiento/activos/{a.id}").status_code == 200
    assert lectura.post("/api/mantenimiento/activos", json={"code": "X", "name": "X"}).status_code == 403
    assert ui_post(lectura, f"/mantenimiento/activos/{a.id}/odometro", {"odometer_km": "99999"}).status_code == 403
    mant = client_for("mantenimiento")
    assert mant.post(f"/mantenimiento/activos/{a.id}/odometro", data={"odometer_km": "99999"}).status_code == 403
    db.expire_all()
    assert db.get(Asset, a.id).odometer_km == 10000
