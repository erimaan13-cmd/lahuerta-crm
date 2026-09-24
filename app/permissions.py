"""RBAC: matriz rol → permisos (RNF-03). Roles inferidos del organigrama (docs/01 §3A)."""

ALL = {
    "lead:read", "lead:write", "lead:convert",
    "account:read", "account:write",
    "opportunity:read", "opportunity:write",
    "activity:write", "task:read", "task:write",
    "case:read", "case:write", "quote:write",
    "email:read", "email:ingest", "email:review",
    "dashboard:read", "audit:read", "integration:run", "export:read", "users:manage",
    # operación interna (2026-09)
    "inventory:read", "inventory:write",
    "sales:read", "sales:write",
    "procurement:read", "procurement:write", "procurement:authorize",
    "hr:read", "hr:write",
    "pettycash:read", "pettycash:write",
    "maintenance:read", "maintenance:write",
    "notification:read", "attachment:write",
}
READ = {p for p in ALL if p.endswith(":read")}
ADMIN_ONLY = {"audit:read", "export:read", "users:manage"}
# Datos personales de empleados: solo RRHH y administradores (E-08, aviso de privacidad pendiente)
HR_ONLY = {"hr:read", "hr:write"}
# Caja chica: montos y comprobantes solo para administración y administradores
CASH_ONLY = {"pettycash:read", "pettycash:write"}
BASE_READ = READ - ADMIN_ONLY - HR_ONLY - CASH_ONLY

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": set(ALL),
    "ventas": BASE_READ | {
        "lead:write", "lead:convert", "account:write", "opportunity:write", "activity:write",
        "task:write", "case:write", "quote:write", "email:review", "sales:write", "attachment:write"},
    "atencion": BASE_READ | {
        "lead:write", "activity:write", "task:write", "case:write", "email:ingest", "email:review",
        "attachment:write"},
    "calidad": BASE_READ | {
        "case:write", "activity:write", "task:write", "email:review", "attachment:write"},
    "administracion": BASE_READ | {
        "case:write", "activity:write", "task:write", "email:ingest", "email:review", "integration:run",
        "pettycash:read", "pettycash:write", "procurement:write", "sales:write", "attachment:write"},
    "almacen": BASE_READ | {"inventory:write", "task:write", "activity:write", "attachment:write"},
    "abastecimiento": BASE_READ | {"procurement:write", "inventory:write", "task:write", "activity:write",
                                   "attachment:write"},
    "rrhh": BASE_READ | HR_ONLY | {"task:write", "activity:write", "attachment:write"},
    "mantenimiento": BASE_READ | {"maintenance:write", "task:write", "activity:write", "attachment:write"},
    "lectura": BASE_READ,
}

ROLE_LABELS = {
    "admin": "Administrador del sistema", "ventas": "Ventas", "atencion": "Atención a clientes",
    "calidad": "Calidad e inocuidad", "administracion": "Administración", "almacen": "Almacén",
    "abastecimiento": "Abastecimiento", "rrhh": "Recursos Humanos", "mantenimiento": "Mantenimiento",
    "lectura": "Solo lectura",
}


def has_permission(role: str | None, perm: str) -> bool:
    return perm in ROLE_PERMISSIONS.get(role or "", set())
