"""Tiempo hábil (RF-34): L–V 8:00–17:00, America/Monterrey (horario publicado, evidencia E13).

Días feriados: descanso obligatorio de la Ley Federal del Trabajo, art. 74 (fijos y "lunes" móviles).
PENDIENTE: validar con La Huerta si descansa otros días (p. ej. jueves/viernes santo, 12-dic).
Las fechas en BD son UTC sin zona; aquí se convierten a hora local solo para el cálculo.
"""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app import config

TZ = ZoneInfo(config.BUSINESS_TZ)
OPEN, CLOSE = time(config.BUSINESS_OPEN_HOUR), time(config.BUSINESS_CLOSE_HOUR)
HOURS_PER_DAY = config.BUSINESS_CLOSE_HOUR - config.BUSINESS_OPEN_HOUR


def _nth_monday(year: int, month: int, n: int) -> date:
    d = date(year, month, 1)
    d += timedelta(days=(7 - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def holidays(year: int) -> set[date]:
    h = {date(year, 1, 1), _nth_monday(year, 2, 1), _nth_monday(year, 3, 3), date(year, 5, 1),
         date(year, 9, 16), _nth_monday(year, 11, 3), date(year, 12, 25)}
    if (year - 2024) % 6 == 0:  # 1-oct: transmisión del Poder Ejecutivo Federal (2024, 2030…)
        h.add(date(year, 10, 1))
    return h | set(config.EXTRA_HOLIDAYS)


def is_business_day(d: date) -> bool:
    return d.weekday() < 5 and d not in holidays(d.year)


def to_local(dt_utc_naive: datetime) -> datetime:
    return dt_utc_naive.replace(tzinfo=timezone.utc).astimezone(TZ)


def to_utc_naive(dt_local: datetime) -> datetime:
    return dt_local.astimezone(timezone.utc).replace(tzinfo=None)


def add_business_hours(start_utc: datetime, hours: float) -> datetime:
    """Suma horas hábiles a un instante UTC (naive) y devuelve UTC (naive)."""
    if hours < 0:
        raise ValueError("hours debe ser ≥ 0")
    cur = to_local(start_utc)
    remaining = timedelta(hours=hours)
    while True:
        if not is_business_day(cur.date()) or cur.time() >= CLOSE:
            nxt = cur.date() + timedelta(days=1)
            while not is_business_day(nxt):
                nxt += timedelta(days=1)
            cur = datetime.combine(nxt, OPEN, TZ)
            continue
        if cur.time() < OPEN:
            cur = datetime.combine(cur.date(), OPEN, TZ)
        end_of_day = datetime.combine(cur.date(), CLOSE, TZ)
        available = end_of_day - cur
        if remaining <= available:
            return to_utc_naive(cur + remaining)
        remaining -= available
        cur = end_of_day  # fuerza el salto al siguiente día hábil


def business_hours_between(start_utc: datetime, end_utc: datetime) -> float:
    """Horas hábiles transcurridas (para medir cumplimiento de SLA)."""
    if end_utc <= start_utc:
        return 0.0
    cur, end = to_local(start_utc), to_local(end_utc)
    total = timedelta()
    while cur < end:
        if is_business_day(cur.date()):
            a = max(cur, datetime.combine(cur.date(), OPEN, TZ))
            b = min(end, datetime.combine(cur.date(), CLOSE, TZ))
            if b > a:
                total += b - a
        cur = datetime.combine(cur.date() + timedelta(days=1), time(0), TZ)
    return round(total.total_seconds() / 3600, 2)
