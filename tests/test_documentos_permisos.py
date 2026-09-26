"""Un adjunto hereda la reserva del módulo dueño (regla 4c, D-40, D-59).

Antes bastaba `dashboard:read` —que tienen los diez roles— para descargar cualquier documento, así que
un usuario de solo lectura podía bajar la identificación de un empleado o un comprobante de caja chica.
Estas pruebas fijan el comportamiento correcto en las tres puertas: descarga, API y listado.
"""
import pytest

from app import config
from app.services import files as files_svc


@pytest.fixture()
def uploads(tmp_path, monkeypatch):
    """Guarda los archivos de prueba fuera de data/uploads."""
    monkeypatch.setattr(config, "UPLOAD_DIR", tmp_path / "uploads")
    return config.UPLOAD_DIR


@pytest.fixture()
def docs(db, uploads):
    """Un documento por cada nivel de reserva.

    Los tres llevan vencimiento a propósito: el listado de /documentos solo muestra los que lo tienen,
    y sin él las comprobaciones de que un documento NO aparece pasarían por vacío.
    """
    vence = "2026-12-31"
    return {
        "empleado": files_svc.save_upload(db, "employee", "e-1", "ine-empleado.pdf", b"datos personales",
                                          None, kind="identificacion", title="INE del empleado",
                                          expires_on=vence),
        "caja": files_svc.save_upload(db, "petty_cash", "f-1", "ticket-caja.pdf", b"comprobante",
                                      None, kind="comprobante", title="Ticket de caja", expires_on=vence),
        "activo": files_svc.save_upload(db, "asset", "a-1", "poliza-camion.pdf", b"poliza",
                                        None, kind="poliza_garantia", title="Poliza del camion",
                                        expires_on=vence),
    }


# ------------------------------------------------------------------ las tres puertas cerradas
@pytest.mark.parametrize("llave", ["empleado", "caja"])
def test_lectura_no_descarga_documento_reservado(client_for, docs, llave):
    c = client_for("lectura")
    assert c.get(f"/documentos/{docs[llave].id}").status_code == 403


@pytest.mark.parametrize("llave", ["empleado", "caja"])
def test_lectura_no_lee_el_documento_por_la_api(client_for, docs, llave):
    c = client_for("lectura")
    assert c.get(f"/api/documentos/{docs[llave].id}").status_code == 403


@pytest.mark.parametrize("tipo", ["employee", "petty_cash"])
def test_lectura_no_lista_por_tipo_reservado(client_for, docs, tipo):
    c = client_for("lectura")
    assert c.get(f"/documentos?entity_type={tipo}").status_code == 403


def test_el_listado_completo_oculta_los_reservados(client_for, docs):
    """Sin filtro la pestaña sigue sirviendo, pero recortada a lo permitido.

    Se comprueba por el título, que es lo que la tabla imprime como enlace.
    """
    html = client_for("lectura").get("/documentos").text
    assert "Poliza del camion" in html  # el de mantenimiento sí lo puede ver
    assert "INE del empleado" not in html
    assert "Ticket de caja" not in html
    assert docs["empleado"].id not in html  # ni el enlace para descargarlo
    assert docs["caja"].id not in html


def test_rrhh_ve_el_del_empleado_en_el_listado_y_no_el_de_caja(client_for, docs):
    html = client_for("rrhh").get("/documentos").text
    assert "INE del empleado" in html
    assert "Ticket de caja" not in html


# ------------------------------------------------------------------ y abiertas para quien le toca
def test_rrhh_si_descarga_el_documento_del_empleado(client_for, docs):
    r = client_for("rrhh").get(f"/documentos/{docs['empleado'].id}")
    assert r.status_code == 200 and r.content == b"datos personales"


def test_administracion_si_descarga_el_comprobante_de_caja(client_for, docs):
    r = client_for("administracion").get(f"/documentos/{docs['caja'].id}")
    assert r.status_code == 200 and r.content == b"comprobante"


def test_rrhh_no_descarga_el_comprobante_de_caja(client_for, docs):
    """La reserva es por módulo, no un permiso general de 'datos delicados'."""
    assert client_for("rrhh").get(f"/documentos/{docs['caja'].id}").status_code == 403


def test_administracion_no_descarga_el_documento_del_empleado(client_for, docs):
    assert client_for("administracion").get(f"/documentos/{docs['empleado'].id}").status_code == 403


def test_admin_descarga_todo(client_for, docs):
    c = client_for("admin")
    for att in docs.values():
        assert c.get(f"/documentos/{att.id}").status_code == 200


# ------------------------------------------------------------------ falla cerrado
def test_tipo_desconocido_solo_lo_ve_el_administrador(db, client_for, uploads):
    """Agregar un entity_type nuevo sin tocar la tabla deja el documento protegido, no expuesto."""
    att = files_svc.save_upload(db, "asset", "x-1", "raro.pdf", b"x", None)
    att.entity_type = "modulo_que_no_existe_todavia"
    db.commit()
    assert client_for("lectura").get(f"/documentos/{att.id}").status_code == 403
    assert client_for("rrhh").get(f"/documentos/{att.id}").status_code == 403
    assert client_for("admin").get(f"/documentos/{att.id}").status_code == 200


def test_la_tabla_cubre_todos_los_tipos_en_uso():
    """Si alguien agrega un entity_type a ENTITY_LABELS, esta prueba obliga a decidir su permiso."""
    faltan = set(files_svc.ENTITY_LABELS) - set(files_svc.ENTITY_READ_PERMISSION)
    assert not faltan, f"tipos sin permiso asignado en ENTITY_READ_PERMISSION: {sorted(faltan)}"
