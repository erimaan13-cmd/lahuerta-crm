"""Gestión de usuarios (solo administradores). Cada cambio queda en la bitácora como evento de seguridad."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record, snapshot
from app.models import User
from app.permissions import ROLE_PERMISSIONS
from app.security import hash_password
from app.services.common import DomainError, get_or_404, norm_email

MIN_PASSWORD = 10


def _active_admins(db: Session) -> int:
    return db.scalar(select(func.count()).where(User.role == "admin", User.is_active.is_(True))) or 0


def create_user(db: Session, data: dict, actor_id: str) -> User:
    email = norm_email((data.get("email") or "").strip())
    name = (data.get("full_name") or "").strip()
    role = data.get("role")
    pw = data.get("password") or ""
    if not email or not name:
        raise DomainError("Correo y nombre son obligatorios")
    if role not in ROLE_PERMISSIONS:
        raise DomainError(f"Rol inválido: {role}")
    if len(pw) < MIN_PASSWORD:
        raise DomainError(f"La contraseña temporal debe tener al menos {MIN_PASSWORD} caracteres")
    if db.scalar(select(User).where(User.email == email)):
        raise DomainError(f"Ya existe un usuario con el correo {email}")
    u = User(email=email, full_name=name, role=role, team=role, password_hash=hash_password(pw))
    db.add(u)
    db.flush()
    record(db, actor_id, "usuario.crear", "user", u.id, after=snapshot(u), category="seguridad",
           summary=f"Alta de {email} con rol {role}")
    db.commit()
    return u


def set_active(db: Session, user_id: str, active: bool, actor_id: str) -> User:
    u = get_or_404(db, User, user_id, "Usuario")
    if u.is_active == active:
        return u
    if not active and u.role == "admin" and _active_admins(db) <= 1:
        raise DomainError("No se puede desactivar al último administrador activo")
    if not active and u.id == actor_id:
        raise DomainError("No puedes desactivar tu propia cuenta")
    before = snapshot(u)
    u.is_active = active
    record(db, actor_id, "usuario.reactivar" if active else "usuario.desactivar", "user", u.id, before, snapshot(u),
           category="seguridad", summary=f"{'Reactivación' if active else 'Desactivación'} de {u.email}")
    db.commit()
    return u


def change_role(db: Session, user_id: str, role: str, actor_id: str) -> User:
    u = get_or_404(db, User, user_id, "Usuario")
    if role not in ROLE_PERMISSIONS:
        raise DomainError(f"Rol inválido: {role}")
    if u.role == "admin" and role != "admin" and _active_admins(db) <= 1:
        raise DomainError("No se puede quitar el rol al último administrador activo")
    before = snapshot(u)
    u.role, u.team = role, role
    record(db, actor_id, "usuario.cambiar_rol", "user", u.id, before, snapshot(u), category="seguridad",
           summary=f"Rol de {u.email}: {before['role']} → {role}")
    db.commit()
    return u


def reset_password(db: Session, user_id: str, new_password: str, actor_id: str) -> User:
    u = get_or_404(db, User, user_id, "Usuario")
    if len(new_password or "") < MIN_PASSWORD:
        raise DomainError(f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres")
    u.password_hash = hash_password(new_password)
    # la contraseña nunca se guarda en la bitácora; solo el hecho
    record(db, actor_id, "usuario.restablecer_contrasena", "user", u.id, category="seguridad",
           summary=f"Contraseña restablecida para {u.email}")
    db.commit()
    return u
