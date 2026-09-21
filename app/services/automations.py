"""Automatizaciones programables. En el MVP se ejecutan bajo demanda (botón / API / CLI); en producción,
con un programador (cron o scheduler) una vez al día. Son idempotentes."""
from datetime import timedelta
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.audit import record
from app.models import Account, OrderReference, Task, utcnow
from app.services.business_time import add_business_hours


def _order_date(o: OrderReference):
    return o.delivered_at or o.promised_date or o.created_at


def reorder_candidates(db: Session, now=None) -> list[dict]:
    """Clientes cuyo siguiente pedido esperado ya pasó (RF-38).
    Esperado = último pedido + intervalo promedio entre pedidos (o REORDER_DEFAULT_DAYS con un solo pedido),
    con una tolerancia de REORDER_TOLERANCE."""
    now = now or utcnow()
    out = []
    for acc in db.scalars(select(Account).where(Account.lifecycle.in_(["cliente_activo", "cliente_recurrente"]))):
        dates = sorted(_order_date(o) for o in acc.orders if o.status != "cancelado")
        if not dates:
            continue
        gaps = [(b - a).days for a, b in zip(dates, dates[1:]) if (b - a).days > 0]
        interval = mean(gaps) if gaps else config.REORDER_DEFAULT_DAYS
        expected = dates[-1] + timedelta(days=interval * (1 + config.REORDER_TOLERANCE))
        if now > expected:
            out.append({"account": acc, "last_order": dates[-1], "interval_days": round(interval, 1),
                        "days_overdue": (now - expected).days})
    return sorted(out, key=lambda x: -x["days_overdue"])


def run_reorder_check(db: Session, actor_id: str | None = None, now=None) -> dict:
    created = skipped = 0
    for c in reorder_candidates(db, now):
        acc = c["account"]
        open_task = db.scalar(select(Task).where(Task.related_type == "account", Task.related_id == acc.id,
                                                 Task.origin == "auto_recompra", Task.status == "pendiente"))
        if open_task:
            skipped += 1
            continue
        db.add(Task(title=f"Recompra: {acc.name} sin pedido desde {c['last_order']:%d/%m} "
                          f"(intervalo habitual {c['interval_days']:g} días)",
                    assignee_role="ventas", assignee_id=acc.owner_id, related_type="account", related_id=acc.id,
                    origin="auto_recompra", priority="alta" if acc.is_key_account else "media",
                    due_at=add_business_hours(now or utcnow(), 9)))
        created += 1
    record(db, actor_id, "automation.reorder_check", "automation", None, after={"created": created, "skipped": skipped})
    db.commit()
    return {"created": created, "skipped_existing": skipped}


if __name__ == "__main__":  # python -m app.services.automations
    from app.db import SessionLocal
    with SessionLocal() as s:
        print(run_reorder_check(s))
