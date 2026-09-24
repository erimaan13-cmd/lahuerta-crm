import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import db as dbmod
from app.db import Base, make_engine
from app.main import app
from app.models import Product, Sector, Supplier, User, Warehouse
from app.security import hash_password

ROLES = ["admin", "ventas", "atencion", "calidad", "administracion", "almacen",
         "abastecimiento", "rrhh", "mantenimiento", "lectura"]
PW = "test-pass"


@pytest.fixture()
def db(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    s = Session()
    for r in ROLES:
        s.add(User(id=f"u-{r}", email=f"{r}@t.local", full_name=r.title(), role=r, password_hash=hash_password(PW)))
    for code in ["industria_alimentaria", "hotel", "restaurante", "comedor_industrial", "otro"]:
        s.add(Sector(code=code, name=code))
    for sku, name, cat, kw in [("ESP-001", "Comino molido", "especia", "comino"),
                               ("ESP-002", "Pimienta negra", "especia", "pimienta"),
                               ("CHI-001", "Chile guajillo", "chile_seco", "guajillo"),
                               ("GRA-001", "Arroz", "grano", "arroz"),
                               ("CON-001", "Sazonador para carnes", "condimento", "sazonador")]:
        s.add(Product(id=sku, sku=sku, name=name, category=cat, keywords=kw, unit="saco",
                      kg_per_unit=25.0, packaging="saco_pp", min_stock_kg=100.0))
    # bodegas y proveedor de prueba para los módulos de operación
    s.add(Warehouse(id="w-mty", code="MTY", name="Bodega Guadalupe"))
    s.add(Warehouse(id="w-tmp", code="TMP", name="Bodega temporal"))
    s.add(Supplier(id="sup-1", name="Especias de Origen (DEMO)", origin="nacional"))
    s.commit()
    app.dependency_overrides[dbmod.get_db] = lambda: (yield from _gen(Session))
    yield s
    s.close()
    app.dependency_overrides.clear()
    engine.dispose()


def _gen(Session):
    x = Session()
    try:
        yield x
    finally:
        x.close()


def csrf(c: TestClient) -> str:
    """Obtiene (o genera) el token CSRF de la cookie del cliente de pruebas."""
    if "crm_csrf" not in c.cookies:
        c.get("/login")
    return c.cookies["crm_csrf"]


def ui_post(c: TestClient, url: str, data: dict | None = None, **kw):
    return c.post(url, data={**(data or {}), "csrf_token": csrf(c)}, **kw)


@pytest.fixture(autouse=True)
def _reset_login_limiter():
    from app import main
    main._login_fails.clear()
    yield
    main._login_fails.clear()


@pytest.fixture()
def client_for(db):
    def make(role: str | None):
        c = TestClient(app)
        if role:
            r = ui_post(c, "/login", {"email": f"{role}@t.local", "password": PW}, follow_redirects=False)
            assert r.status_code == 303, r.text
        return c
    return make


@pytest.fixture()
def admin(client_for):
    return client_for("admin")
