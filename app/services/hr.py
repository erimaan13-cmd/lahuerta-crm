"""Recursos Humanos: expedientes, descripciones de puesto y contratos (E-08).

Por qué este diseño:
- El expediente **nunca se borra**: una baja cambia el estado a "baja" para conservar la historia
  laboral (obligación documental y requisito de FSSC 22000).
- La descripción del puesto se guarda **por puntos**: una función por línea en `duties` y un
  requisito por línea en `requirements`. La interfaz las muestra como viñetas; guardarlas como texto
  con saltos de línea evita una tabla más para algo que el cliente edita a mano.
- Un empleado tiene **un solo contrato vigente**: renovar cierra el anterior como "renovado" y crea
  el nuevo, para que la cadena de contratos quede completa y el aviso de vencimiento no se duplique.
- Los datos personales solo los ven RRHH y administradores (permisos hr:read / hr:write); cada
  consulta queda en la bitácora por el middleware de acceso.
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import config
from app.audit import record
from app.models import Employee, EmploymentContract, JobProfile, User, utcnow
from app.services.common import DomainError, get_or_404, norm_email, norm_phone
from app.services.files import parse_date

CONTRACT_TYPES = {"temporal": "Temporal", "indeterminado": "Por tiempo indeterminado"}
CONTRACT_STATUS = {"vigente": "Vigente", "renovado": "Renovado", "terminado": "Terminado"}
EMPLOYEE_STATUS = {"activo": "Activo", "baja": "Baja"}


def bullets(text: str | None) -> list[str]:
    """Convierte el texto por líneas en viñetas (una función o requisito por renglón)."""
    return [line.strip(" -•\t") for line in (text or "").splitlines() if line.strip(" -•\t")]


def _clean_lines(value: str | None) -> str:
    """Normaliza lo que escribió el usuario: una línea por punto, sin viñetas repetidas ni vacíos."""
    return "\n".join(bullets(value))


# ------------------------------------------------------------------ puestos
def create_job_profile(db: Session, data: dict, actor_id: str | None) -> JobProfile:
    title = (data.get("title") or "").strip()
    if not title:
        raise DomainError("El puesto necesita un nombre")
    if db.scalar(select(JobProfile).where(JobProfile.title == title)):
        raise DomainError(f"Ya existe el puesto «{title}»")
    duties = _clean_lines(data.get("duties"))
    if not duties:
        raise DomainError("La descripción del puesto necesita al menos una función (una por renglón)")
    jp = JobProfile(title=title[:160], area=(data.get("area") or "").strip() or None, duties=duties,
                    requirements=_clean_lines(data.get("requirements")))
    db.add(jp)
    db.flush()
    record(db, actor_id, "puesto.alta", "job_profile", jp.id,
           after={"puesto": jp.title, "area": jp.area, "funciones": len(bullets(jp.duties)),
                  "requisitos": len(bullets(jp.requirements))},
           summary=f"Puesto creado: {jp.title}")
    db.commit()
    return jp


def update_job_profile(db: Session, job_profile_id: str, data: dict, actor_id: str | None) -> JobProfile:
    jp = get_or_404(db, JobProfile, job_profile_id, "Puesto")
    before = {"area": jp.area, "funciones": bullets(jp.duties), "requisitos": bullets(jp.requirements)}
    if "area" in data:
        jp.area = (data.get("area") or "").strip() or None
    if data.get("duties"):
        jp.duties = _clean_lines(data["duties"])
    if "requirements" in data:
        jp.requirements = _clean_lines(data.get("requirements"))
    record(db, actor_id, "puesto.cambio", "job_profile", jp.id, before=before,
           after={"area": jp.area, "funciones": bullets(jp.duties), "requisitos": bullets(jp.requirements)},
           summary=f"Puesto actualizado: {jp.title}")
    db.commit()
    return jp


def job_profiles(db: Session) -> list[JobProfile]:
    return list(db.scalars(select(JobProfile).order_by(JobProfile.area, JobProfile.title)))


# ------------------------------------------------------------------ empleados
def create_employee(db: Session, data: dict, actor_id: str | None) -> Employee:
    number = (data.get("employee_no") or "").strip().upper()
    name = (data.get("full_name") or "").strip()
    if not number or not name:
        raise DomainError("El empleado necesita número y nombre completo")
    if db.scalar(select(Employee).where(Employee.employee_no == number)):
        raise DomainError(f"Ya existe un empleado con el número {number}")
    profile = None
    if data.get("job_profile_id"):
        profile = get_or_404(db, JobProfile, data["job_profile_id"], "Puesto")
    if data.get("user_id"):
        get_or_404(db, User, data["user_id"], "Usuario del sistema")
    e = Employee(employee_no=number[:20], full_name=name[:200],
                 area=(data.get("area") or (profile.area if profile else None) or None),
                 job_profile_id=profile.id if profile else None,
                 position_text=(data.get("position_text") or (profile.title if profile else None) or None),
                 hired_on=parse_date(data.get("hired_on")) or utcnow(),
                 phone=norm_phone(data.get("phone") or None), email=norm_email(data.get("email") or None),
                 user_id=data.get("user_id") or None, notes=data.get("notes") or None)
    db.add(e)
    db.flush()
    record(db, actor_id, "empleado.alta", "employee", e.id,
           after={"numero": e.employee_no, "nombre": e.full_name, "area": e.area, "puesto": e.position_text,
                  "ingreso": e.hired_on.date().isoformat() if e.hired_on else None},
           summary=f"Alta de empleado: {e.employee_no} — {e.full_name}")
    db.commit()
    return e


def update_employee(db: Session, employee_id: str, data: dict, actor_id: str | None) -> Employee:
    e = get_or_404(db, Employee, employee_id, "Empleado")
    before = {"area": e.area, "puesto": e.position_text, "telefono": e.phone, "correo": e.email,
              "usuario": e.user_id, "ingreso": e.hired_on.date().isoformat() if e.hired_on else None}
    if data.get("job_profile_id") is not None and "job_profile_id" in data:
        if data["job_profile_id"]:
            profile = get_or_404(db, JobProfile, data["job_profile_id"], "Puesto")
            e.job_profile_id, e.position_text = profile.id, data.get("position_text") or profile.title
        else:
            e.job_profile_id = None
    if data.get("full_name"):
        e.full_name = data["full_name"].strip()[:200]
    if "area" in data:
        e.area = (data.get("area") or "").strip() or None
    if data.get("position_text"):
        e.position_text = data["position_text"].strip()[:160]
    if "phone" in data:
        e.phone = norm_phone(data.get("phone") or None)
    if "email" in data:
        e.email = norm_email(data.get("email") or None)
    if "user_id" in data:
        if data.get("user_id"):
            get_or_404(db, User, data["user_id"], "Usuario del sistema")
        e.user_id = data.get("user_id") or None
    if data.get("hired_on"):
        e.hired_on = parse_date(data["hired_on"])
    if "notes" in data:
        e.notes = data.get("notes") or None
    record(db, actor_id, "empleado.cambio", "employee", e.id, before=before,
           after={"area": e.area, "puesto": e.position_text, "telefono": e.phone, "correo": e.email,
                  "usuario": e.user_id, "ingreso": e.hired_on.date().isoformat() if e.hired_on else None},
           summary=f"Expediente actualizado: {e.full_name}")
    db.commit()
    return e


def terminate(db: Session, employee_id: str, fecha, motivo: str | None, actor_id: str | None) -> Employee:
    """Da de baja al empleado. El expediente se conserva: solo cambia el estado (E-08)."""
    e = get_or_404(db, Employee, employee_id, "Empleado")
    if e.status == "baja":
        raise DomainError(f"{e.full_name} ya está dado de baja")
    if not (motivo or "").strip():
        raise DomainError("La baja necesita motivo")
    day = parse_date(fecha) if not hasattr(fecha, "date") else fecha
    day = day or utcnow()
    e.status = "baja"
    # El modelo no tiene columna de fecha/motivo de baja: se conserva en las notas y en la bitácora.
    e.notes = f"{e.notes + chr(10) if e.notes else ''}Baja {day.date().isoformat()}: {motivo.strip()}"
    cerrados = 0
    for c in db.scalars(select(EmploymentContract).where(EmploymentContract.employee_id == e.id,
                                                         EmploymentContract.status == "vigente")):
        c.status, c.end_on = "terminado", c.end_on or day
        cerrados += 1
    record(db, actor_id, "empleado.baja", "employee", e.id, before={"estado": "activo"},
           after={"estado": "baja", "fecha": day.date().isoformat(), "motivo": motivo.strip(),
                  "contratos_cerrados": cerrados},
           summary=f"Baja de {e.full_name}: {motivo.strip()}")
    db.commit()
    return e


def employees(db: Session, area: str | None = None, status: str | None = None) -> list[Employee]:
    stmt = select(Employee)
    if area:
        stmt = stmt.where(Employee.area == area)
    if status:
        stmt = stmt.where(Employee.status == status)
    return list(db.scalars(stmt.order_by(Employee.status, Employee.area, Employee.full_name)))


def areas(db: Session) -> list[str]:
    return sorted({a for (a,) in db.execute(select(Employee.area).distinct()).all() if a})


# ------------------------------------------------------------------ contratos
def current_contract(db: Session, employee_id: str) -> EmploymentContract | None:
    return db.scalar(select(EmploymentContract).where(EmploymentContract.employee_id == employee_id,
                                                      EmploymentContract.status == "vigente")
                     .order_by(EmploymentContract.start_on.desc()))


def _contract_dates(data: dict, tipo: str) -> tuple:
    start = parse_date(data.get("start_on")) or utcnow()
    end = parse_date(data.get("end_on"))
    if tipo == "temporal" and end is None:
        raise DomainError("Un contrato temporal necesita fecha de término")
    if end and end <= start:
        raise DomainError("La fecha de término debe ser posterior a la de inicio")
    return start, end


def add_contract(db: Session, employee_id: str, data: dict, actor_id: str | None) -> EmploymentContract:
    e = get_or_404(db, Employee, employee_id, "Empleado")
    if e.status == "baja":
        raise DomainError(f"{e.full_name} está dado de baja: no se le puede registrar un contrato nuevo")
    tipo = data.get("type") or "temporal"
    if tipo not in CONTRACT_TYPES:
        raise DomainError(f"Tipo de contrato no válido: {tipo}")
    if current_contract(db, e.id):
        raise DomainError(f"{e.full_name} ya tiene un contrato vigente: renuévalo o termínalo primero")
    start, end = _contract_dates(data, tipo)
    c = EmploymentContract(employee_id=e.id, type=tipo, start_on=start, end_on=end,
                           notes=(data.get("notes") or None))
    db.add(c)
    db.flush()
    record(db, actor_id, "contrato.alta", "employee", e.id,
           after={"contrato_id": c.id, "tipo": c.type, "inicio": start.date().isoformat(),
                  "fin": end.date().isoformat() if end else None},
           summary=f"Contrato {CONTRACT_TYPES[tipo].lower()} de {e.full_name}")
    db.commit()
    return c


def renew_contract(db: Session, contract_id: str, data: dict, actor_id: str | None) -> EmploymentContract:
    """Marca el contrato anterior como "renovado" y crea el nuevo, sin perder la cadena."""
    old = get_or_404(db, EmploymentContract, contract_id, "Contrato")
    if old.status != "vigente":
        raise DomainError(f"Solo se renueva un contrato vigente (este está {CONTRACT_STATUS.get(old.status, old.status).lower()})")
    tipo = data.get("type") or old.type
    if tipo not in CONTRACT_TYPES:
        raise DomainError(f"Tipo de contrato no válido: {tipo}")
    data = dict(data)
    if not data.get("start_on") and old.end_on:
        data["start_on"] = (old.end_on + timedelta(days=1)).date().isoformat()
    start, end = _contract_dates(data, tipo)
    if start < old.start_on:
        raise DomainError("El contrato nuevo no puede empezar antes que el anterior")
    old.status = "renovado"
    nuevo = EmploymentContract(employee_id=old.employee_id, type=tipo, start_on=start, end_on=end,
                               notes=(data.get("notes") or None))
    db.add(nuevo)
    db.flush()
    record(db, actor_id, "contrato.renovacion", "employee", old.employee_id,
           before={"contrato_id": old.id, "estado": "vigente"},
           after={"contrato_anterior": old.id, "estado_anterior": "renovado", "contrato_id": nuevo.id,
                  "tipo": nuevo.type, "inicio": start.date().isoformat(),
                  "fin": end.date().isoformat() if end else None},
           summary=f"Contrato renovado de {old.employee.full_name}")
    db.commit()
    return nuevo


def end_contract(db: Session, contract_id: str, data: dict, actor_id: str | None) -> EmploymentContract:
    c = get_or_404(db, EmploymentContract, contract_id, "Contrato")
    if c.status == "terminado":
        raise DomainError("El contrato ya está terminado")
    motivo = (data.get("reason") or data.get("notes") or "").strip()
    day = parse_date(data.get("end_on")) or utcnow()
    c.status, c.end_on = "terminado", day
    if motivo:
        c.notes = f"{c.notes + ' · ' if c.notes else ''}{motivo}"[:300]
    record(db, actor_id, "contrato.termino", "employee", c.employee_id,
           after={"contrato_id": c.id, "fin": day.date().isoformat(), "motivo": motivo or None},
           summary=f"Contrato terminado de {c.employee.full_name}")
    db.commit()
    return c


def contracts_expiring(db: Session, days: int | None = None) -> list[EmploymentContract]:
    """Contratos vigentes que vencen dentro de N días (o ya vencidos). Alimenta el aviso semanal."""
    limit = utcnow() + timedelta(days=days if days is not None else config.CONTRACT_ALERT_DAYS)
    return list(db.scalars(select(EmploymentContract).where(EmploymentContract.status == "vigente",
                                                            EmploymentContract.end_on.is_not(None),
                                                            EmploymentContract.end_on <= limit)
                           .order_by(EmploymentContract.end_on)))


def without_current_contract(db: Session) -> list[Employee]:
    vigentes = {c.employee_id for c in db.scalars(select(EmploymentContract)
                                                  .where(EmploymentContract.status == "vigente"))}
    return [e for e in employees(db, status="activo") if e.id not in vigentes]


# ------------------------------------------------------------------ tablero
def metrics(db: Session) -> dict:
    rows = dict(db.execute(select(Employee.area, func.count()).where(Employee.status == "activo")
                           .group_by(Employee.area)).all())
    desde = utcnow() - timedelta(days=30)
    altas = db.scalar(select(func.count()).select_from(Employee).where(Employee.hired_on >= desde)) or 0
    bajas = db.scalar(select(func.count()).select_from(Employee).where(Employee.status == "baja")) or 0
    return {"activos": sum(rows.values()), "bajas": bajas, "altas_30d": altas,
            "por_area": {(a or "Sin área"): n for a, n in sorted(rows.items(), key=lambda kv: -kv[1])},
            "contratos_por_vencer": len(contracts_expiring(db)),
            "sin_contrato_vigente": len(without_current_contract(db)),
            "puestos": db.scalar(select(func.count()).select_from(JobProfile)) or 0}
