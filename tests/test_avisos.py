"""Pantalla de avisos (E-12): ver, marcar leído, silenciar, reactivar y generar.

El envío por correo no tiene adaptador: los avisos quedan en cola con estado "sin_adaptador".
"""
from datetime import timedelta

from sqlalchemy import select

from app.models import AuditEvent, Notification, NotificationMute, User, utcnow
from app.services import hr
from app.services import notifications as avisos
from tests.conftest import ui_post

EMPLEADO = {"employee_no": "EMP-100", "full_name": "Rosa Lara (DEMO)", "area": "Calidad"}


def _con_contrato_por_vencer(db, dias: int = 30):
    e = hr.create_employee(db, dict(EMPLEADO), "u-rrhh")
    hoy = utcnow()
    hr.add_contract(db, e.id, {"type": "temporal", "start_on": hoy.date().isoformat(),
                               "end_on": (hoy + timedelta(days=dias)).date().isoformat()}, "u-rrhh")
    avisos.generate(db, "u-admin")
    db.expire_all()
    return e, db.scalar(select(Notification).where(Notification.kind == "contrato_por_vencer"))


def acciones(db, **filtros):
    db.expire_all()
    stmt = select(AuditEvent).order_by(AuditEvent.seq)
    for k, v in filtros.items():
        stmt = stmt.where(getattr(AuditEvent, k) == v)
    return [e.action for e in db.scalars(stmt)]


# ------------------------------------------------------------------ pantalla
def test_la_pantalla_lista_filtra_y_avisa_que_el_correo_no_esta_configurado(client_for, db):
    e, aviso = _con_contrato_por_vencer(db)
    html = client_for("rrhh").get("/avisos").text
    assert "Rosa Lara (DEMO)" in html and f"/rrhh/empleados/{e.id}" in html
    assert "sin_adaptador" in html and "adaptador de correo no está configurado" in html
    assert 'class="chip warn"' in html                     # severidad con chip de color

    c = client_for("admin")
    assert "Rosa Lara (DEMO)" in c.get("/avisos?kind=contrato_por_vencer").text
    assert "Rosa Lara (DEMO)" not in c.get("/avisos?kind=tarea_vencida").text
    assert "Rosa Lara (DEMO)" not in c.get("/avisos?status=leida").text


def test_marcar_leido_desde_la_interfaz_y_por_api(client_for, db):
    e, aviso = _con_contrato_por_vencer(db)
    r = ui_post(client_for("rrhh"), f"/avisos/{aviso.id}/leido", follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    leido = db.get(Notification, aviso.id)
    assert leido.status == "leida" and leido.read_by == "u-rrhh" and leido.read_at
    assert "aviso.leido" in acciones(db, entity_id=aviso.id)

    admin = db.get(User, "u-admin")
    assert any(a.id == aviso.id for a in avisos.listing(db, admin, None))  # sigue consultable con "todos"
    assert avisos.pending_count(db, admin) == len(avisos.listing(db, admin, "pendiente"))


def test_silenciar_30_dias_y_reactivar(client_for, db):
    e, aviso = _con_contrato_por_vencer(db)
    clave, aviso_id = aviso.mute_key, aviso.id   # se guardan: abajo se borran las filas de avisos
    c = client_for("rrhh")
    r = ui_post(c, "/avisos/silenciar", {"mute_key": clave, "days": "30",
                                         "reason": "Renovación ya acordada"}, follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    m = db.get(NotificationMute, clave)
    assert m and m.until and m.muted_by == "u-rrhh" and m.reason == "Renovación ya acordada"
    assert db.get(Notification, aviso_id).status == "leida"

    db.execute(Notification.__table__.delete())
    db.commit()
    db.expunge_all()
    avisos.generate(db, "u-admin")                          # silenciado: no vuelve a aparecer
    assert db.scalars(select(Notification).where(Notification.kind == "contrato_por_vencer")).all() == []

    assert ui_post(c, "/avisos/reactivar", {"mute_key": clave}, follow_redirects=False).status_code == 303
    db.expire_all()
    assert db.get(NotificationMute, clave) is None
    avisos.generate(db, "u-admin")
    assert db.scalars(select(Notification).where(Notification.kind == "contrato_por_vencer")).all()
    assert {"aviso.silenciado", "aviso.reactivado"} <= set(acciones(db, category="sistema"))


def test_silenciar_sin_fecha(client_for, db):
    e, aviso = _con_contrato_por_vencer(db)
    ui_post(client_for("rrhh"), "/avisos/silenciar", {"mute_key": aviso.mute_key, "days": ""},
            follow_redirects=False)
    db.expire_all()
    assert db.get(NotificationMute, aviso.mute_key).until is None


# ------------------------------------------------------------------ generar
def test_generar_requiere_permiso_y_no_duplica(client_for, db):
    e, aviso = _con_contrato_por_vencer(db)
    assert ui_post(client_for("lectura"), "/avisos/generar", follow_redirects=False).status_code == 403
    assert client_for("lectura").post("/api/avisos/generar", json={}).status_code == 403

    r = client_for("administracion").post("/api/avisos/generar", json={})   # tiene integration:run
    assert r.status_code == 200 and r.json()["created"]["contrato_por_vencer"] == 0
    db.expire_all()
    assert len(db.scalars(select(Notification).where(Notification.kind == "contrato_por_vencer")).all()) == 1

    ui_post(client_for("admin"), "/avisos/generar", follow_redirects=False)
    db.expire_all()
    assert len(db.scalars(select(Notification).where(Notification.kind == "contrato_por_vencer")).all()) == 1


def test_api_de_avisos(client_for, db):
    e, aviso = _con_contrato_por_vencer(db)
    c = client_for("rrhh")
    datos = c.get("/api/avisos?kind=contrato_por_vencer").json()
    assert len(datos) == 1 and datos[0]["email_status"] == "sin_adaptador"
    assert c.post(f"/api/avisos/{aviso.id}/leido").json()["aviso"]["status"] == "leida"


def test_sin_sesion_no_se_ven_los_avisos(client_for, db):
    _con_contrato_por_vencer(db)
    sin_sesion = client_for(None)
    assert sin_sesion.get("/avisos", follow_redirects=False).status_code == 303   # manda a /login
    assert sin_sesion.get("/api/avisos").status_code == 401
