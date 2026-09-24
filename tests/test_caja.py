"""Caja chica (E-09): fondo fijo, comprobante obligatorio y exportación para el contador.

Datos sintéticos marcados (DEMO).
"""
import pytest
from sqlalchemy import select

from app.models import AuditEvent, PettyCashEntry
from app.services import pettycash as caja
from app.services.common import DomainError
from tests.conftest import ui_post

TICKET = {"file": ("ticket.pdf", b"%PDF-1.4 comprobante demo", "application/pdf")}


@pytest.fixture(autouse=True)
def _uploads_en_tmp(tmp_path, monkeypatch):
    """Los comprobantes de prueba no deben tocar la carpeta real de archivos."""
    monkeypatch.setattr("app.config.UPLOAD_DIR", tmp_path / "uploads")


@pytest.fixture()
def fondo(db):
    return caja.create_fund(db, {"name": "Caja chica oficina (DEMO)", "fund_amount_mxn": "5000",
                                 "responsible_user_id": "u-administracion"}, "u-admin")


def acciones(db, **filtros):
    db.expire_all()
    stmt = select(AuditEvent).order_by(AuditEvent.seq)
    for k, v in filtros.items():
        stmt = stmt.where(getattr(AuditEvent, k) == v)
    return [e.action for e in db.scalars(stmt)]


def gasto(c, fund_id, monto="1200", descripcion="Papelería del mes (DEMO)", **kw):
    return ui_post(c, f"/caja/{fund_id}/gastos",
                   {"amount_mxn": monto, "category": "papeleria", "description": descripcion},
                   follow_redirects=False, **kw)


# ------------------------------------------------------------------ permisos
def test_lectura_no_escribe_y_sin_csrf_se_rechaza(client_for, fondo, db):
    # La caja chica solo la ve administración y los administradores (D-40): son montos y comprobantes.
    assert client_for("lectura").get("/caja").status_code == 403
    assert client_for("administracion").get("/caja").status_code == 200
    assert gasto(client_for("lectura"), fondo.id, files=TICKET).status_code == 403
    sin_csrf = client_for("administracion").post(f"/caja/{fondo.id}/gastos",
                                                 data={"amount_mxn": "10", "description": "x"}, files=TICKET)
    assert sin_csrf.status_code == 403 and "CSRF" in sin_csrf.text
    assert caja.balance(db, fondo.id) == 5000.0


# ------------------------------------------------------------------ comprobante obligatorio y saldo
def test_gasto_sin_comprobante_se_rechaza(client_for, fondo, db):
    r = gasto(client_for("administracion"), fondo.id)                   # sin archivo adjunto
    assert r.status_code == 422 and "comprobante" in r.text
    assert db.scalars(select(PettyCashEntry)).all() == []
    with pytest.raises(DomainError, match="comprobante"):
        caja.add_expense(db, fondo.id, {"amount_mxn": 100, "description": "x"}, "u-admin")


def test_el_saldo_baja_con_el_gasto_y_sube_con_la_reposicion(client_for, fondo, db):
    c = client_for("administracion")
    assert gasto(c, fondo.id, "1200", files=TICKET).status_code == 303
    assert caja.balance(db, fondo.id) == 3800.0

    r = ui_post(c, f"/caja/{fondo.id}/reposiciones",
                {"amount_mxn": "1200", "description": "Reposición contra comprobantes (DEMO)"},
                follow_redirects=False)
    assert r.status_code == 303
    assert caja.balance(db, fondo.id) == 5000.0

    pantalla = c.get(f"/caja/{fondo.id}").text
    assert "Papelería del mes (DEMO)" in pantalla and "Reposición contra comprobantes (DEMO)" in pantalla
    assert "saldo $5,000.00" in pantalla

    mov = db.scalars(select(PettyCashEntry).where(PettyCashEntry.type == "gasto")).one()
    assert mov.receipt_id and mov.category == "papeleria" and mov.actor_id == "u-administracion"
    assert {"caja.gasto", "caja.reposicion"} <= set(acciones(db, entity_id=fondo.id))


def test_gasto_mayor_al_saldo_se_rechaza(client_for, fondo, db):
    r = gasto(client_for("administracion"), fondo.id, "9000", files=TICKET)
    assert r.status_code == 422 and "negativo" in r.text
    assert caja.balance(db, fondo.id) == 5000.0
    with pytest.raises(DomainError, match="mayor que cero"):
        caja.add_expense(db, fondo.id, {"amount_mxn": 0, "description": "x"}, "u-admin", receipt_id="x")


def test_api_saldo_y_reposicion(client_for, fondo, db):
    c = client_for("administracion")
    assert c.get("/api/caja").json()[0]["saldo_mxn"] == 5000.0
    r = c.post(f"/api/caja/{fondo.id}/reposiciones", json={"amount_mxn": 500, "description": "Extra (DEMO)"})
    assert r.status_code == 201 and r.json()["saldo_mxn"] == 5500.0
    assert c.get(f"/api/caja/{fondo.id}/saldo").json() == {"caja": fondo.name, "fondo_mxn": 5000.0,
                                                           "saldo_mxn": 5500.0}


# ------------------------------------------------------------------ exportación para el contador
def test_el_csv_trae_las_filas_del_periodo(client_for, fondo, db):
    from datetime import timedelta

    from app.models import utcnow
    c = client_for("administracion")
    gasto(c, fondo.id, "300", "Limpieza (DEMO)", files=TICKET)

    r = c.get(f"/caja/{fondo.id}.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    cuerpo = r.content.decode("utf-8-sig")
    lineas = [ln for ln in cuerpo.splitlines() if ln]
    assert lineas[0] == "fecha,caja,tipo,categoria,monto_mxn,descripcion,responsable,comprobante"
    assert len(lineas) == 2 and "Limpieza (DEMO)" in lineas[1] and lineas[1].endswith("sí")
    assert "300.00" in lineas[1]

    hoy = utcnow().date().isoformat()
    ayer = (utcnow() - timedelta(days=1)).date().isoformat()
    vacio = c.get(f"/caja/{fondo.id}.csv?desde={ayer}&hasta={ayer}").content.decode("utf-8-sig")
    assert len([ln for ln in vacio.splitlines() if ln]) == 1        # solo el encabezado
    lleno = c.get(f"/caja/{fondo.id}.csv?desde={hoy}&hasta={hoy}").content.decode("utf-8-sig")
    assert "Limpieza (DEMO)" in lleno                                # el día "hasta" se incluye completo


# ------------------------------------------------------------------ tablero y catálogo
def test_metricas_por_caja_y_categoria(client_for, fondo, db):
    c = client_for("administracion")
    gasto(c, fondo.id, "200", "Papelería (DEMO)", files=TICKET)
    m = caja.metrics(db)
    assert m["cajas_activas"] == 1 and m["saldo_por_caja"][fondo.name] == 4800.0
    assert m["gasto_mes_por_categoria"] == {"Papelería": 200.0} and m["gasto_total_mxn"] == 200.0
    html = c.get("/caja").text
    assert fondo.name in html and "Papelería" in html


def test_nombre_de_caja_unico_y_responsable_valido(db):
    caja.create_fund(db, {"name": "Caja única (DEMO)", "fund_amount_mxn": "1000"}, "u-admin")
    with pytest.raises(DomainError, match="Ya existe una caja"):
        caja.create_fund(db, {"name": "Caja única (DEMO)", "fund_amount_mxn": "1000"}, "u-admin")
    with pytest.raises(DomainError, match="Usuario responsable"):
        caja.create_fund(db, {"name": "Otra (DEMO)", "fund_amount_mxn": "1000",
                              "responsible_user_id": "no-existe"}, "u-admin")
