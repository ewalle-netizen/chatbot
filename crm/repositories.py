"""Repository classes encapsulating persistence logic."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models


class ClientRepository:
    """Data access layer for :class:`~crm.models.Client`."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, name: str, external_id: Optional[str] = None, industry: Optional[str] = None) -> models.Client:
        client = models.Client(name=name, external_id=external_id, industry=industry)
        self.session.add(client)
        return client

    def get_by_external_id(self, external_id: str) -> Optional[models.Client]:
        stmt = select(models.Client).where(models.Client.external_id == external_id)
        return self.session.scalar(stmt)


class OpportunityRepository:
    """Data access layer for :class:`~crm.models.Opportunity`."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        client: models.Client,
        name: str,
        expected_close_date: Optional[date],
        amount: float,
        owner: Optional[str],
        stage: models.OpportunityStage = models.OpportunityStage.prospect,
        probability: float = 0,
        infor_sales_order_id: Optional[str] = None,
    ) -> models.Opportunity:
        opportunity = models.Opportunity(
            client=client,
            name=name,
            expected_close_date=expected_close_date,
            amount=amount,
            owner=owner,
            stage=stage,
            probability=probability,
            infor_sales_order_id=infor_sales_order_id,
        )
        self.session.add(opportunity)
        return opportunity

    def get(self, opportunity_id) -> Optional[models.Opportunity]:
        return self.session.get(models.Opportunity, opportunity_id)

    def list_open(self) -> List[models.Opportunity]:
        stmt = select(models.Opportunity).where(models.Opportunity.stage != models.OpportunityStage.won)
        return self.session.scalars(stmt).all()

    def get_by_infor_id(self, external_id: str) -> Optional[models.Opportunity]:
        stmt = select(models.Opportunity).where(models.Opportunity.infor_sales_order_id == external_id)
        return self.session.scalar(stmt)


class InvoiceRepository:
    """Data access layer for :class:`~crm.models.Invoice`."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_from_payload(
        self,
        *,
        opportunity: models.Opportunity,
        external_id: str,
        amount: float,
        issue_date: date,
        due_date: Optional[date],
        status: models.InvoiceStatus,
        currency: str,
    ) -> models.Invoice:
        stmt = select(models.Invoice).where(models.Invoice.external_id == external_id)
        invoice = self.session.scalar(stmt)
        if invoice is None:
            invoice = models.Invoice(
                opportunity=opportunity,
                external_id=external_id,
                amount=amount,
                issue_date=issue_date,
                due_date=due_date,
                status=status,
                currency=currency,
                last_sync_at=datetime.utcnow(),
            )
            self.session.add(invoice)
        else:
            invoice.amount = amount
            invoice.issue_date = issue_date
            invoice.due_date = due_date
            invoice.status = status
            invoice.currency = currency
            invoice.last_sync_at = datetime.utcnow()
        return invoice


class SalesDateUpdateRepository:
    """Repository for :class:`~crm.models.SalesDateUpdate`."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        *,
        opportunity: models.Opportunity,
        previous_date: Optional[date],
        new_date: date,
        updated_by: str,
        synced_with_infor: bool,
        sync_reference: Optional[str],
    ) -> models.SalesDateUpdate:
        entry = models.SalesDateUpdate(
            opportunity=opportunity,
            previous_date=previous_date,
            new_date=new_date,
            updated_by=updated_by,
            synced_with_infor=synced_with_infor,
            sync_reference=sync_reference,
        )
        self.session.add(entry)
        return entry


class SyncLogRepository:
    """Repository for :class:`~crm.models.SyncLog`."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, sync_type: str, success: bool, details: Optional[str] = None) -> models.SyncLog:
        log = models.SyncLog(sync_type=sync_type, success=success, details=details)
        self.session.add(log)
        return log
