"""Adaptador ERP (RF-22). El CRM solo guarda referencias/estados de pedidos (D-09).
El adaptador real dependerá del sistema que use La Huerta (DESCONOCIDO)."""
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record
from app.models import Account, IntegrationEvent, OrderReference


@dataclass
class ErpOrder:
    erp_order_id: str
    erp_customer_ref: str
    status: str
    promised_date: datetime | None
    delivered_at: datetime | None
    total_kg: float | None


class ErpAdapter(Protocol):
    name: str

    def fetch_orders(self) -> list[ErpOrder]: ...


class MockErpAdapter:
    name = "erp_mock"

    def __init__(self, orders: list[ErpOrder]):
        self._orders = orders

    def fetch_orders(self) -> list[ErpOrder]:
        return list(self._orders)


def sync_orders(db: Session, adapter: ErpAdapter, actor_id: str | None = None) -> dict:
    """Upsert idempotente de OrderReference + recálculo del lifecycle de la cuenta."""
    created = updated = skipped = 0
    for o in adapter.fetch_orders():
        acc = db.scalar(select(Account).where(Account.erp_customer_ref == o.erp_customer_ref))
        if acc is None:
            skipped += 1
            db.add(IntegrationEvent(direction="in", system="erp", event_type="order.unmatched_customer",
                                    payload={"erp_order_id": o.erp_order_id, "customer": o.erp_customer_ref},
                                    status="error", error="Cliente ERP sin cuenta en el CRM"))
            continue
        ref = db.scalar(select(OrderReference).where(OrderReference.source_system == adapter.name,
                                                     OrderReference.erp_order_id == o.erp_order_id))
        if ref is None:
            ref = OrderReference(erp_order_id=o.erp_order_id, source_system=adapter.name, status=o.status)
            acc.orders.append(ref)  # relación en memoria sincronizada para recalcular el lifecycle
            created += 1
        else:
            updated += 1
        ref.status, ref.promised_date, ref.delivered_at, ref.total_kg = (
            o.status, o.promised_date, o.delivered_at, o.total_kg)
        db.flush()
        n_orders = len([r for r in acc.orders if r.status != "cancelado"])
        acc.lifecycle = "cliente_recurrente" if n_orders >= 2 else ("cliente_activo" if n_orders else acc.lifecycle)
    db.add(IntegrationEvent(direction="in", system="erp", event_type="orders.sync", status="procesado",
                            payload={"created": created, "updated": updated, "skipped": skipped}))
    record(db, actor_id, "integration.erp_sync", "integration", None,
           after={"created": created, "updated": updated, "skipped": skipped})
    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}
