"""Recursos Humanos (E-08): expedientes reservados a RRHH y administradores, contratos y avisos.

Datos sintéticos marcados (DEMO): ninguna persona real.
"""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import AuditEvent, Employee, EmploymentContract, Notification, utcnow
from app.services import hr
from app.services import notifications as avisos
from app.services.common import DomainError
from tests.conftest import ui_post

EMPLEADO = {"employee_no": "EMP-001", "full_name": "Ana Pérez (DEMO)", "area": "Producción",
            "position_text": "Auxiliar de empaque", "phone": "8112345678", "email": "ana@lahuerta.example"}


def acciones(db, **filtros):
    db.expire_all()
    stmt = select(AuditEvent).order_by(AuditEvent.seq)
    for k, v in filtros.items():
        stmt = stmt.where(getattr(AuditEvent, k) == v)
    return [e.action for e in db.scalars(stmt)]


def _contrato(dias: int) -> dict:
    """Contrato temporal que vence dentro de N días."""
    hoy = utcnow()
    return {"type": "temporal", "start_on": hoy.date().isoformat(),
            "end_on": (hoy + timedelta(days=dias)).date().isoformat()}


# ------------------------------------------------------------------ permisos: información personal
def test_solo_rrhh_y_admin_ven_los_expedientes(client_for, db):
    e = hr.create_employee(db, dict(EMPLEADO), "u-admin")
    for rol in ["ventas", "atencion", "calidad", "administracion", "almacen", "abastecimiento",
                "mantenimiento", "lectura"]:
        c = client_for(rol)
        assert c.get("/rrhh").status_code == 403, rol
        assert c.get(f"/rrhh/empleados/{e.id}").status_code == 403, rol
        assert c.get("/api/rrhh/empleados").status_code == 403, rol
    for rol in ["rrhh", "admin"]:
        assert client_for(rol).get("/rrhh").status_code == 200, rol


def test_lectura_no_puede_escribir_y_sin_csrf_se_rechaza(client_for, db):
    assert ui_post(client_for("lectura"), "/rrhh/empleados", dict(EMPLEADO)).status_code == 403
    sin_csrf = client_for("rrhh").post("/rrhh/empleados", data=dict(EMPLEADO))
    assert sin_csrf.status_code == 403 and "CSRF" in sin_csrf.text
    assert db.scalar(select(Employee).where(Employee.employee_no == "EMP-001")) is None


def test_el_expediente_muestra_el_aviso_de_privacidad(client_for, db):
    e = hr.create_employee(db, dict(EMPLEADO), "u-admin")
    html = client_for("rrhh").get(f"/rrhh/empleados/{e.id}").text
    assert "Aviso de privacidad" in html and "Recursos Humanos" in html


# ------------------------------------------------------------------ alta, puesto por viñetas y baja
def test_alta_desde_la_interfaz_con_puesto_por_vinetas(client_for, db):
    c = client_for("rrhh")
    r = ui_post(c, "/rrhh/puestos", {"title": "Auxiliar de empaque (DEMO)", "area": "Producción",
                                     "duties": "Pesar producto\nEtiquetar cajas\n\n- Limpiar su estación",
                                     "requirements": "Secundaria terminada"}, follow_redirects=False)
    assert r.status_code == 303
    puesto = hr.job_profiles(db)[0]
    assert hr.bullets(puesto.duties) == ["Pesar producto", "Etiquetar cajas", "Limpiar su estación"]
    assert "<li>Etiquetar cajas</li>" in c.get("/rrhh/puestos").text

    assert ui_post(c, "/rrhh/empleados", {**EMPLEADO, "job_profile_id": puesto.id},
                   follow_redirects=False).status_code == 303
    e = db.scalar(select(Employee).where(Employee.employee_no == "EMP-001"))
    assert e.area == "Producción" and e.status == "activo" and e.phone == "8112345678"
    assert "Etiquetar cajas" in c.get(f"/rrhh/empleados/{e.id}").text
    assert {"puesto.alta", "empleado.alta"} <= set(acciones(db, category="negocio"))


def test_numero_de_empleado_unico_y_baja_conserva_el_expediente(db):
    e = hr.create_employee(db, dict(EMPLEADO), "u-rrhh")
    with pytest.raises(DomainError, match="Ya existe un empleado"):
        hr.create_employee(db, {**EMPLEADO, "full_name": "Otra persona (DEMO)"}, "u-rrhh")
    hr.add_contract(db, e.id, _contrato(90), "u-rrhh")
    hr.terminate(db, e.id, None, "Renuncia voluntaria", "u-rrhh")
    db.expire_all()
    e = db.get(Employee, e.id)
    assert e.status == "baja" and "Renuncia voluntaria" in e.notes          # el expediente sigue ahí
    assert hr.current_contract(db, e.id) is None                            # y su contrato quedó cerrado
    with pytest.raises(DomainError, match="ya está dado de baja"):
        hr.terminate(db, e.id, None, "otra vez", "u-rrhh")
    assert "empleado.baja" in acciones(db, entity_id=e.id)


def test_la_baja_exige_motivo(db):
    e = hr.create_employee(db, dict(EMPLEADO), "u-rrhh")
    with pytest.raises(DomainError, match="motivo"):
        hr.terminate(db, e.id, None, "", "u-rrhh")


# ------------------------------------------------------------------ contratos
def test_renovar_deja_el_anterior_en_renovado(client_for, db):
    e = hr.create_employee(db, dict(EMPLEADO), "u-rrhh")
    viejo = hr.add_contract(db, e.id, _contrato(30), "u-rrhh")
    with pytest.raises(DomainError, match="ya tiene un contrato vigente"):
        hr.add_contract(db, e.id, _contrato(60), "u-rrhh")

    fin = (utcnow() + timedelta(days=200)).date().isoformat()
    r = ui_post(client_for("rrhh"), f"/rrhh/contratos/{viejo.id}/renovar",
                {"type": "temporal", "end_on": fin}, follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    assert db.get(EmploymentContract, viejo.id).status == "renovado"
    nuevo = hr.current_contract(db, e.id)
    assert nuevo and nuevo.id != viejo.id and nuevo.status == "vigente"
    assert nuevo.start_on.date() == (viejo.end_on + timedelta(days=1)).date()  # encadena sin huecos
    assert "contrato.renovacion" in acciones(db, entity_id=e.id)
    with pytest.raises(DomainError, match="vigente"):
        hr.renew_contract(db, viejo.id, {"end_on": fin}, "u-rrhh")


def test_contrato_temporal_necesita_fecha_de_termino(db):
    e = hr.create_employee(db, dict(EMPLEADO), "u-rrhh")
    with pytest.raises(DomainError, match="fecha de término"):
        hr.add_contract(db, e.id, {"type": "temporal", "start_on": utcnow().date().isoformat()}, "u-rrhh")
    c = hr.add_contract(db, e.id, {"type": "indeterminado", "start_on": utcnow().date().isoformat()}, "u-rrhh")
    assert c.end_on is None and c.status == "vigente"


def test_contratos_por_vencer_y_metricas(db):
    e1 = hr.create_employee(db, dict(EMPLEADO), "u-rrhh")
    e2 = hr.create_employee(db, {**EMPLEADO, "employee_no": "EMP-002", "full_name": "Luis Soto (DEMO)",
                                 "area": "Almacén", "email": "luis@lahuerta.example",
                                 "phone": "8187654321"}, "u-rrhh")
    hr.add_contract(db, e1.id, _contrato(30), "u-rrhh")      # entra en la ventana de 60 días
    hr.add_contract(db, e2.id, _contrato(400), "u-rrhh")     # todavía no
    por_vencer = hr.contracts_expiring(db)
    assert [c.employee_id for c in por_vencer] == [e1.id]
    m = hr.metrics(db)
    assert m["activos"] == 2 and m["por_area"] == {"Producción": 1, "Almacén": 1}
    assert m["contratos_por_vencer"] == 1 and m["sin_contrato_vigente"] == 0
    e3 = hr.create_employee(db, {**EMPLEADO, "employee_no": "EMP-003", "full_name": "Mar Ruiz (DEMO)",
                                 "email": None, "phone": None}, "u-rrhh")
    assert hr.metrics(db)["sin_contrato_vigente"] == 1 and e3.status == "activo"


# ------------------------------------------------------------------ avisos de contrato
def test_contrato_a_30_dias_genera_aviso_sin_duplicar_y_se_puede_silenciar(client_for, db):
    e = hr.create_employee(db, dict(EMPLEADO), "u-rrhh")
    c = hr.add_contract(db, e.id, _contrato(30), "u-rrhh")

    avisos.generate(db, "u-admin")
    pendientes = db.scalars(select(Notification).where(Notification.kind == "contrato_por_vencer")).all()
    assert len(pendientes) == 1
    aviso = pendientes[0]
    assert aviso.entity_id == e.id and aviso.target_role == "rrhh" and aviso.severity == "warn"
    assert aviso.link == f"/rrhh/empleados/{e.id}" and aviso.email_status == "sin_adaptador"
    assert "Ana Pérez (DEMO)" in aviso.title

    avisos.generate(db, "u-admin")  # correrlo otra vez no duplica (dedupe_key incluye la semana)
    db.expire_all()
    assert len(db.scalars(select(Notification).where(Notification.kind == "contrato_por_vencer")).all()) == 1

    avisos.mute(db, f"contrato:{c.id}", 30, "u-rrhh", "Ya se acordó la renovación")
    db.expire_all()
    assert db.get(Notification, aviso.id).status == "leida"   # el pendiente se cierra al silenciar
    db.execute(Notification.__table__.delete())               # aunque llegue otra semana…
    db.commit()
    avisos.generate(db, "u-admin")
    assert db.scalars(select(Notification).where(Notification.kind == "contrato_por_vencer")).all() == []


def test_api_de_contratos_por_vencer(client_for, db):
    e = hr.create_employee(db, dict(EMPLEADO), "u-rrhh")
    hr.add_contract(db, e.id, _contrato(20), "u-rrhh")
    datos = client_for("rrhh").get("/api/rrhh/contratos-por-vencer").json()
    assert len(datos) == 1 and datos[0]["empleado"] == "Ana Pérez (DEMO)" and datos[0]["status"] == "vigente"


def test_api_alta_de_empleado_queda_en_bitacora(client_for, db):
    r = client_for("rrhh").post("/api/rrhh/empleados", json={**EMPLEADO, "employee_no": "EMP-009"})
    assert r.status_code == 201
    eid = r.json()["employee"]["id"]
    assert "empleado.alta" in acciones(db, entity_id=eid)
    assert all(e.actor_id == "u-rrhh" for e in db.scalars(select(AuditEvent).where(AuditEvent.entity_id == eid)))
