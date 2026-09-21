"""Modelo de dominio del CRM (ver docs/02_PLAN.md §3).

Regla D-09: pedidos, inventario, lotes y facturas NO son maestros aquí; solo referencias.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(30))  # admin|ventas|atencion|calidad|administracion|lectura
    team: Mapped[str | None] = mapped_column(String(60))
    password_hash: Mapped[str] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Sector(Base):
    __tablename__ = "sectors"
    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    sku: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(30))  # especia|grano|semilla|chile_seco|condimento
    keywords: Mapped[str] = mapped_column(Text, default="")  # sinónimos separados por coma
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), index=True)
    domain: Mapped[str | None] = mapped_column(String(120), unique=True, index=True)
    sector_code: Mapped[str | None] = mapped_column(ForeignKey("sectors.code"))
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(80))
    lifecycle: Mapped[str] = mapped_column(String(30), default="prospecto")
    is_key_account: Mapped[bool] = mapped_column(Boolean, default=False)
    erp_customer_ref: Mapped[str | None] = mapped_column(String(60))
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    contacts: Mapped[list["Contact"]] = relationship(back_populates="account")
    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="account")
    orders: Mapped[list["OrderReference"]] = relationship(back_populates="account")
    cases: Mapped[list["Case"]] = relationship(back_populates="account")


class Contact(Base, TimestampMixin):
    __tablename__ = "contacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), index=True)
    job_title: Mapped[str | None] = mapped_column(String(120))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    account: Mapped[Account] = relationship(back_populates="contacts")


class Lead(Base, TimestampMixin):
    __tablename__ = "leads"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    full_name: Mapped[str] = mapped_column(String(200))
    company_name: Mapped[str | None] = mapped_column(String(200), index=True)
    email: Mapped[str | None] = mapped_column(String(200), index=True)
    phone: Mapped[str | None] = mapped_column(String(30), index=True)
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(80))
    sector_code: Mapped[str | None] = mapped_column(ForeignKey("sectors.code"))
    product_interest_text: Mapped[str | None] = mapped_column(String(300))
    volume_band: Mapped[str] = mapped_column(String(20), default="desconocido")
    est_volume_kg: Mapped[float | None] = mapped_column(Float)
    message: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30), default="otro")
    campaign: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="nuevo", index=True)
    discard_reason: Mapped[str | None] = mapped_column(String(200))
    below_minimum: Mapped[bool] = mapped_column(Boolean, default=False)
    possible_duplicate_of_id: Mapped[str | None] = mapped_column(ForeignKey("leads.id"))
    duplicate_reason: Mapped[str | None] = mapped_column(String(120))
    converted_account_id: Mapped[str | None] = mapped_column(ForeignKey("accounts.id"))
    converted_contact_id: Mapped[str | None] = mapped_column(ForeignKey("contacts.id"))
    converted_opportunity_id: Mapped[str | None] = mapped_column(ForeignKey("opportunities.id"))
    merged_into_id: Mapped[str | None] = mapped_column(ForeignKey("leads.id"))
    consent_source: Mapped[str | None] = mapped_column(String(120))
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class Opportunity(Base, TimestampMixin):
    __tablename__ = "opportunities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), index=True)
    contact_id: Mapped[str | None] = mapped_column(ForeignKey("contacts.id"))
    title: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(30), default="estandar")
    stage: Mapped[str] = mapped_column(String(30), default="requerimiento", index=True)
    est_volume_kg: Mapped[float | None] = mapped_column(Float)
    est_value_mxn: Mapped[float | None] = mapped_column(Float)
    expected_close: Mapped[datetime | None] = mapped_column(DateTime)
    lost_reason: Mapped[str | None] = mapped_column(String(200))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[Account] = relationship(back_populates="opportunities")
    interests: Mapped[list["ProductInterest"]] = relationship(back_populates="opportunity",
                                                              cascade="all, delete-orphan")
    quotes: Mapped[list["Quote"]] = relationship(back_populates="opportunity")


class ProductInterest(Base):
    __tablename__ = "product_interests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    est_kg: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(String(300))  # especificación: molienda, malla…
    opportunity: Mapped[Opportunity] = relationship(back_populates="interests")
    product: Mapped[Product] = relationship()


class Quote(Base, TimestampMixin):
    __tablename__ = "quotes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), index=True)
    folio: Mapped[str] = mapped_column(String(20), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="borrador")
    valid_until: Mapped[datetime | None] = mapped_column(DateTime)
    currency: Mapped[str] = mapped_column(String(3), default="MXN")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    opportunity: Mapped[Opportunity] = relationship(back_populates="quotes")
    items: Mapped[list["QuoteItem"]] = relationship(back_populates="quote", cascade="all, delete-orphan")

    @property
    def total_mxn(self) -> float:
        return round(sum(i.qty_kg * i.unit_price_mxn for i in self.items), 2)

    @property
    def total_kg(self) -> float:
        return round(sum(i.qty_kg for i in self.items), 2)


class QuoteItem(Base):
    __tablename__ = "quote_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    quote_id: Mapped[str] = mapped_column(ForeignKey("quotes.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    qty_kg: Mapped[float] = mapped_column(Float)
    packaging: Mapped[str] = mapped_column(String(30))  # saco_pp_pead|saco_kraft_pe|caja_corrugado
    unit_price_mxn: Mapped[float] = mapped_column(Float)
    quote: Mapped[Quote] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()


class OrderReference(Base, TimestampMixin):
    """Espejo de un pedido del ERP. Solo lo escribe el adaptador de integración."""
    __tablename__ = "order_references"
    __table_args__ = (UniqueConstraint("source_system", "erp_order_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), index=True)
    opportunity_id: Mapped[str | None] = mapped_column(ForeignKey("opportunities.id"))
    erp_order_id: Mapped[str] = mapped_column(String(60), index=True)
    status: Mapped[str] = mapped_column(String(20))
    promised_date: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    total_kg: Mapped[float | None] = mapped_column(Float)
    source_system: Mapped[str] = mapped_column(String(30), default="erp_mock")
    account: Mapped[Account] = relationship(back_populates="orders")


class Case(Base, TimestampMixin):
    __tablename__ = "cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    folio: Mapped[str] = mapped_column(String(20), unique=True)
    account_id: Mapped[str | None] = mapped_column(ForeignKey("accounts.id"), index=True)
    contact_id: Mapped[str | None] = mapped_column(ForeignKey("contacts.id"))
    lead_id: Mapped[str | None] = mapped_column(ForeignKey("leads.id"))
    type: Mapped[str] = mapped_column(String(30))
    severity: Mapped[str] = mapped_column(String(10), default="media")
    status: Mapped[str] = mapped_column(String(20), default="abierto", index=True)
    subject: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    lot_reference: Mapped[str | None] = mapped_column(String(60))
    order_ref: Mapped[str | None] = mapped_column(String(60))
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    account: Mapped[Account | None] = relationship(back_populates="cases")


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    type: Mapped[str] = mapped_column(String(20))  # llamada|correo|whatsapp|reunion|nota|sistema
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    related_type: Mapped[str] = mapped_column(String(20), index=True)
    related_id: Mapped[str] = mapped_column(String(36), index=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(200))
    due_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pendiente", index=True)
    priority: Mapped[str] = mapped_column(String(10), default="media")
    assignee_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    assignee_role: Mapped[str | None] = mapped_column(String(30))
    related_type: Mapped[str | None] = mapped_column(String(20))
    related_id: Mapped[str | None] = mapped_column(String(36))
    origin: Mapped[str] = mapped_column(String(30), default="manual")


class EmailMessage(Base, TimestampMixin):
    __tablename__ = "email_messages"
    __table_args__ = (UniqueConstraint("provider", "provider_message_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    provider: Mapped[str] = mapped_column(String(30))
    provider_message_id: Mapped[str] = mapped_column(String(300))
    thread_id: Mapped[str | None] = mapped_column(String(300))
    from_email: Mapped[str] = mapped_column(String(200), index=True)
    from_name: Mapped[str | None] = mapped_column(String(200))
    to: Mapped[str | None] = mapped_column(String(300))
    subject: Mapped[str] = mapped_column(String(300), default="")
    body_text: Mapped[str] = mapped_column(Text, default="")
    body_clean: Mapped[str] = mapped_column(Text, default="")
    received_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_hash: Mapped[str | None] = mapped_column(String(64))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    classification: Mapped["EmailClassification"] = relationship(back_populates="email", uselist=False)


class EmailClassification(Base, TimestampMixin):
    __tablename__ = "email_classifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email_id: Mapped[str] = mapped_column(ForeignKey("email_messages.id"), unique=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    margin: Mapped[float] = mapped_column(Float, default=0.0)
    method: Mapped[str] = mapped_column(String(20), default="rules")
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    extracted_entities: Mapped[dict] = mapped_column(JSON, default=dict)
    suggested_owner_role: Mapped[str | None] = mapped_column(String(30))
    suggested_action: Mapped[str | None] = mapped_column(String(60))
    suggested_action_label: Mapped[str | None] = mapped_column(String(200))
    crm_link_type: Mapped[str | None] = mapped_column(String(20))
    crm_link_id: Mapped[str | None] = mapped_column(String(36))
    crm_links: Mapped[dict] = mapped_column(JSON, default=dict)
    review_status: Mapped[str] = mapped_column(String(20), index=True)
    review_reason: Mapped[str | None] = mapped_column(String(200))
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    final_category: Mapped[str | None] = mapped_column(String(40))
    applied_entity_type: Mapped[str | None] = mapped_column(String(20))
    applied_entity_id: Mapped[str | None] = mapped_column(String(36))
    classifier_version: Mapped[str] = mapped_column(String(20))
    email: Mapped[EmailMessage] = relationship(back_populates="classification")


class IntegrationEvent(Base, TimestampMixin):
    __tablename__ = "integration_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    direction: Mapped[str] = mapped_column(String(3))  # in|out
    system: Mapped[str] = mapped_column(String(20))
    event_type: Mapped[str] = mapped_column(String(60))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="pendiente")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)


class AuditEvent(Base):
    """Bitácora solo-inserción y encadenada (RNF-05). Registra acciones de negocio, accesos y eventos de
    seguridad de todos los usuarios. El ORM impide editarla o borrarla (ver app/audit.py) y cada fila lleva
    el hash de la anterior: cualquier alteración directa en la BD se detecta con verify_chain()."""
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    seq: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), index=True)
    actor_email: Mapped[str | None] = mapped_column(String(200))
    actor_role: Mapped[str | None] = mapped_column(String(30), index=True)
    category: Mapped[str] = mapped_column(String(20), default="negocio", index=True)  # negocio|acceso|seguridad|sistema
    action: Mapped[str] = mapped_column(String(60), index=True)
    entity_type: Mapped[str] = mapped_column(String(30), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), index=True)
    summary: Mapped[str | None] = mapped_column(String(300))
    before: Mapped[dict | None] = mapped_column(JSON)
    after: Mapped[dict | None] = mapped_column(JSON)
    ip: Mapped[str | None] = mapped_column(String(64))
    method: Mapped[str | None] = mapped_column(String(8))
    path: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[int | None] = mapped_column(Integer)
    request_id: Mapped[str | None] = mapped_column(String(40))
    prev_hash: Mapped[str | None] = mapped_column(String(64))
    hash: Mapped[str | None] = mapped_column(String(64))
