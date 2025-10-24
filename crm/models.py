"""Database models representing CRM entities."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class GUIDColumn(Column):
    """Utility column type that stores UUIDs in a portable way."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("primary_key", True)
        kwargs.setdefault("default", uuid.uuid4)
        super().__init__(UUID(as_uuid=True), *args, **kwargs)


class Client(Base):
    __tablename__ = "clients"

    id = GUIDColumn()
    name = Column(String(255), nullable=False)
    external_id = Column(String(255), unique=True, nullable=True)
    industry = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    contacts = relationship("Contact", back_populates="client", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="client", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id = GUIDColumn()
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    role = Column(String(128), nullable=True)

    client = relationship("Client", back_populates="contacts")


class OpportunityStage(str, PyEnum):
    prospect = "prospect"
    proposal = "proposal"
    negotiation = "negotiation"
    won = "won"
    lost = "lost"


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = GUIDColumn()
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    stage = Column(SQLEnum(OpportunityStage), default=OpportunityStage.prospect, nullable=False)
    probability = Column(Numeric(5, 2), nullable=False, default=0)
    expected_close_date = Column(Date, nullable=True)
    actual_close_date = Column(Date, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False, default=0)
    owner = Column(String(255), nullable=True)
    infor_sales_order_id = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    client = relationship("Client", back_populates="opportunities")
    invoices = relationship("Invoice", back_populates="opportunity", cascade="all, delete-orphan")
    sales_date_updates = relationship(
        "SalesDateUpdate",
        back_populates="opportunity",
        cascade="all, delete-orphan",
        order_by="SalesDateUpdate.updated_at",
    )


class InvoiceStatus(str, PyEnum):
    draft = "draft"
    issued = "issued"
    paid = "paid"
    overdue = "overdue"


class Invoice(Base):
    __tablename__ = "invoices"

    id = GUIDColumn()
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    external_id = Column(String(255), unique=True, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.issued, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    last_sync_at = Column(DateTime, nullable=True)

    opportunity = relationship("Opportunity", back_populates="invoices")


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = GUIDColumn()
    sync_type = Column(String(64), nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    success = Column(Boolean, default=True, nullable=False)
    details = Column(Text, nullable=True)


class SalesDateUpdate(Base):
    __tablename__ = "sales_date_updates"

    id = GUIDColumn()
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    previous_date = Column(Date, nullable=True)
    new_date = Column(Date, nullable=False)
    updated_by = Column(String(255), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    synced_with_infor = Column(Boolean, default=False, nullable=False)
    sync_reference = Column(String(255), nullable=True)

    opportunity = relationship("Opportunity", back_populates="sales_date_updates")
