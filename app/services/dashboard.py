"""Métricas del dashboard mínimo (RF-17). Consultas agregadas en SQL portable."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.classifier.taxonomy import CATEGORIES
from app.models import (Account, Case, EmailClassification, Lead, Opportunity, Quote, Task, utcnow)
from app.services.pipeline import OPEN_STAGES, STAGE_LABELS


def _group(db, col):
    return dict(db.execute(select(col, func.count()).group_by(col)).all())


def metrics(db: Session) -> dict:
    now = utcnow()
    pipeline_rows = db.execute(select(Opportunity.stage, func.count(), func.coalesce(func.sum(Opportunity.est_volume_kg), 0),
                                      func.coalesce(func.sum(Opportunity.est_value_mxn), 0))
                               .group_by(Opportunity.stage)).all()
    pipeline = {s: {"label": STAGE_LABELS[s], "count": 0, "kg": 0.0, "mxn": 0.0} for s in STAGE_LABELS}
    for stage, n, kg, mxn in pipeline_rows:
        pipeline[stage] = {"label": STAGE_LABELS.get(stage, stage), "count": n, "kg": float(kg), "mxn": float(mxn)}
    open_value = sum(v["mxn"] for k, v in pipeline.items() if k in OPEN_STAGES)
    email_cats = _group(db, EmailClassification.category)
    return {
        "leads_by_status": _group(db, Lead.status),
        "leads_by_source": _group(db, Lead.source),
        "leads_below_minimum": db.scalar(select(func.count()).where(Lead.below_minimum.is_(True), Lead.status != "descartado")),
        "leads_possible_duplicates": db.scalar(select(func.count()).where(Lead.possible_duplicate_of_id.is_not(None))),
        "pipeline": pipeline,
        "open_pipeline_mxn": open_value,
        "tasks_pending": db.scalar(select(func.count()).where(Task.status == "pendiente")),
        "tasks_overdue": db.scalar(select(func.count()).where(Task.status == "pendiente", Task.due_at < now)),
        "emails_by_category": {CATEGORIES.get(k, {}).get("label", k): v for k, v in email_cats.items()},
        "emails_by_review": _group(db, EmailClassification.review_status),
        "needs_review": db.scalar(select(func.count()).where(EmailClassification.review_status == "needs_review")),
        "accounts_by_lifecycle": _group(db, Account.lifecycle),
        "customers": db.scalar(select(func.count()).where(Account.lifecycle.in_(["cliente_activo", "cliente_recurrente"]))),
        "quotes_by_status": _group(db, Quote.status),
        "cases_open": db.scalar(select(func.count()).where(Case.status.not_in(["resuelto", "cerrado"]))),
        "cases_by_type": _group(db, Case.type),
    }
