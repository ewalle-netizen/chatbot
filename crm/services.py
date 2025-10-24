"""Business services for CRM workflows."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .integration.skyline_client import InforSkylineClient
from .models import InvoiceStatus, OpportunityStage
from .repositories import (
    ClientRepository,
    InvoiceRepository,
    OpportunityRepository,
    SalesDateUpdateRepository,
    SyncLogRepository,
)
from .schemas import InvoiceRead, OpportunityRead, OpportunityReport, SalesDashboard


class CRMService:
    """High-level API that coordinates repositories and integrations."""

    def __init__(self, session: Session, skyline_client: Optional[InforSkylineClient] = None) -> None:
        self.session = session
        self.clients = ClientRepository(session)
        self.opportunities = OpportunityRepository(session)
        self.invoices = InvoiceRepository(session)
        self.sales_updates = SalesDateUpdateRepository(session)
        self.sync_logs = SyncLogRepository(session)
        self.skyline_client = skyline_client or InforSkylineClient()

    # ------------------------------------------------------------------
    # Client and opportunity management
    # ------------------------------------------------------------------
    def create_client(
        self,
        *,
        name: str,
        external_id: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> models.Client:
        return self.clients.create(name=name, external_id=external_id, industry=industry)

    def create_opportunity(
        self,
        *,
        client: models.Client,
        name: str,
        expected_close_date: Optional[date],
        amount: float,
        owner: Optional[str],
        stage: OpportunityStage = OpportunityStage.prospect,
        probability: float = 0,
        infor_sales_order_id: Optional[str] = None,
    ) -> models.Opportunity:
        return self.opportunities.create(
            client=client,
            name=name,
            expected_close_date=expected_close_date,
            amount=amount,
            owner=owner,
            stage=stage,
            probability=probability,
            infor_sales_order_id=infor_sales_order_id,
        )

    # ------------------------------------------------------------------
    # Sales date updates
    # ------------------------------------------------------------------
    def update_sales_date(self, *, opportunity_id, new_date: date, updated_by: str) -> models.Opportunity:
        if isinstance(opportunity_id, str):
            try:
                opportunity_id = uuid.UUID(opportunity_id)
            except ValueError as exc:
                raise ValueError("Invalid opportunity id") from exc

        opportunity = self.opportunities.get(opportunity_id)
        if opportunity is None:
            raise ValueError(f"Opportunity {opportunity_id} not found")

        previous_date = opportunity.expected_close_date
        opportunity.expected_close_date = new_date
        opportunity.updated_at = datetime.utcnow()

        sync_reference: Optional[str] = None
        synced_with_infor = False
        if opportunity.infor_sales_order_id:
            response = self.skyline_client.update_sale_date(
                sales_order_id=opportunity.infor_sales_order_id,
                new_date=new_date,
            )
            synced_with_infor = response.success
            sync_reference = response.reference
            if not response.success:
                raise RuntimeError(response.message or "Failed to update Infor Skyline")

        self.sales_updates.record(
            opportunity=opportunity,
            previous_date=previous_date,
            new_date=new_date,
            updated_by=updated_by,
            synced_with_infor=synced_with_infor,
            sync_reference=sync_reference,
        )

        return opportunity

    # ------------------------------------------------------------------
    # Invoice synchronisation
    # ------------------------------------------------------------------
    def synchronise_invoices(self, *, since: Optional[date] = None) -> dict:
        since = since or (datetime.utcnow() - timedelta(days=1)).date()
        processed = 0
        errors = []
        try:
            for payload in self.skyline_client.fetch_invoices(since=since):
                opportunity = self.opportunities.get_by_infor_id(payload.opportunity_external_id)
                if opportunity is None:
                    errors.append(f"Unknown opportunity for invoice {payload.external_id}")
                    continue
                try:
                    status = InvoiceStatus(payload.status)
                except ValueError:
                    try:
                        status = InvoiceStatus(payload.status.lower())
                    except ValueError:
                        status = InvoiceStatus.issued
                self.invoices.upsert_from_payload(
                    opportunity=opportunity,
                    external_id=payload.external_id,
                    amount=payload.amount,
                    issue_date=payload.issue_date,
                    due_date=payload.due_date,
                    status=status,
                    currency=payload.currency,
                )
                processed += 1
            details = f"Processed {processed} invoices"
            if errors:
                details = f"{details}; warnings: {' | '.join(errors)}"
            self.sync_logs.create(sync_type="invoice", success=not errors, details=details)
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(str(exc))
            self.sync_logs.create(sync_type="invoice", success=False, details="; ".join(errors))
            raise
        return {"processed": processed, "warnings": errors}

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def build_sales_dashboard(self) -> SalesDashboard:
        total_open_pipeline = 0.0
        total_invoiced = 0.0
        total_paid = 0.0
        overdue_invoices = 0

        for opportunity in self.opportunities.list_open():
            total_open_pipeline += float(opportunity.amount)

        invoices = self.session.execute(select(models.Invoice)).scalars().all()
        for invoice in invoices:
            amount = float(invoice.amount)
            total_invoiced += amount
            if invoice.status == InvoiceStatus.paid:
                total_paid += amount
            if invoice.status == InvoiceStatus.overdue:
                overdue_invoices += 1

        return SalesDashboard(
            total_open_pipeline=total_open_pipeline,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            overdue_invoices=overdue_invoices,
        )

    def build_opportunity_report(self, *, opportunity_id) -> OpportunityReport:
        if isinstance(opportunity_id, str):
            try:
                opportunity_id = uuid.UUID(opportunity_id)
            except ValueError as exc:
                raise ValueError("Invalid opportunity id") from exc

        opportunity = self.opportunities.get(opportunity_id)
        if opportunity is None:
            raise ValueError(f"Opportunity {opportunity_id} not found")

        invoices = list(opportunity.invoices)
        return OpportunityReport(
            opportunity=OpportunityRead.model_validate(opportunity),
            invoices=[InvoiceRead.model_validate(invoice) for invoice in invoices],
        )
