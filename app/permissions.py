"""RBAC: matriz rol → permisos (RNF-03). Roles inferidos del organigrama (docs/01 §3A)."""

ALL = {
    "lead:read", "lead:write", "lead:convert",
    "account:read", "account:write",
    "opportunity:read", "opportunity:write",
    "activity:write", "task:read", "task:write",
    "case:read", "case:write", "quote:write",
    "email:read", "email:ingest", "email:review",
    "dashboard:read", "audit:read", "integration:run", "export:read", "users:manage",
}
READ = {p for p in ALL if p.endswith(":read")}
ADMIN_ONLY = {"audit:read", "export:read", "users:manage"}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": set(ALL),
    "ventas": READ - ADMIN_ONLY | {
        "lead:write", "lead:convert", "account:write", "opportunity:write", "activity:write",
        "task:write", "case:write", "quote:write", "email:review"},
    "atencion": READ - ADMIN_ONLY | {
        "lead:write", "activity:write", "task:write", "case:write", "email:ingest", "email:review"},
    "calidad": READ - ADMIN_ONLY | {
        "case:write", "activity:write", "task:write", "email:review"},
    "administracion": READ - ADMIN_ONLY | {
        "case:write", "activity:write", "task:write", "email:ingest", "email:review", "integration:run"},
    "lectura": READ - ADMIN_ONLY,
}

ROLE_LABELS = {
    "admin": "Administrador del sistema", "ventas": "Ventas", "atencion": "Atención a clientes",
    "calidad": "Calidad e inocuidad", "administracion": "Administración", "lectura": "Solo lectura",
}


def has_permission(role: str | None, perm: str) -> bool:
    return perm in ROLE_PERMISSIONS.get(role or "", set())
