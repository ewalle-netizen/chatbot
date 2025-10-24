"""Client abstraction to interact with Infor Skyline REST endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, List, Optional

import requests

from ..config import settings


@dataclass
class InvoicePayload:
    """Structured invoice information returned by Infor Skyline."""

    external_id: str
    opportunity_external_id: str
    amount: float
    issue_date: date
    due_date: Optional[date]
    status: str
    currency: str = "USD"


@dataclass
class SaleDateUpdateResponse:
    """Result of sending a sale date update to Infor Skyline."""

    success: bool
    reference: Optional[str]
    message: Optional[str] = None


class InforSkylineClient:
    """Minimal API client encapsulating REST operations used by the CRM."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url or settings.infor_base_url
        self.client_id = client_id or settings.infor_client_id
        self.client_secret = client_secret or settings.infor_client_secret
        self.tenant = tenant or settings.infor_tenant
        self.session = session or requests.Session()

    # ------------------------------------------------------------------
    # Mock helpers
    # ------------------------------------------------------------------
    def _mock_invoices(self, *, since: date) -> List[InvoicePayload]:
        """Return deterministic invoices when mock mode is enabled."""

        return [
            InvoicePayload(
                external_id="INV-1001",
                opportunity_external_id="OPP-100",
                amount=12500.0,
                issue_date=since,
                due_date=since,
                status="issued",
            ),
            InvoicePayload(
                external_id="INV-1002",
                opportunity_external_id="OPP-101",
                amount=9800.5,
                issue_date=since,
                due_date=since,
                status="paid",
            ),
        ]

    def _mock_sale_date_update(self, *, sales_order_id: str, new_date: date) -> SaleDateUpdateResponse:
        reference = f"MOCK-{sales_order_id}-{new_date.isoformat()}"
        return SaleDateUpdateResponse(success=True, reference=reference, message="Mock update successful")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fetch_invoices(self, *, since: date) -> Iterable[InvoicePayload]:
        """Retrieve invoices created or updated since the provided date."""

        if settings.infor_mock_mode:
            return self._mock_invoices(since=since)

        url = f"{self.base_url}/invoices"
        response = self.session.get(
            url,
            params={"updated_since": since.isoformat(), "tenant": self.tenant},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        invoices: List[InvoicePayload] = []
        for invoice in payload:
            invoices.append(
                InvoicePayload(
                    external_id=invoice["invoiceNumber"],
                    opportunity_external_id=invoice["opportunityId"],
                    amount=float(invoice["amount"]),
                    issue_date=datetime.fromisoformat(invoice["issueDate"]).date(),
                    due_date=datetime.fromisoformat(invoice["dueDate"]).date()
                    if invoice.get("dueDate")
                    else None,
                    status=invoice.get("status", "issued"),
                    currency=invoice.get("currency", "USD"),
                )
            )
        return invoices

    def update_sale_date(self, *, sales_order_id: str, new_date: date) -> SaleDateUpdateResponse:
        """Send a sales date update to Infor Skyline."""

        if settings.infor_mock_mode:
            return self._mock_sale_date_update(sales_order_id=sales_order_id, new_date=new_date)

        url = f"{self.base_url}/sales-orders/{sales_order_id}/dates"
        payload = {"committedDate": new_date.isoformat(), "tenant": self.tenant}
        response = self.session.patch(url, json=payload, timeout=30)
        if response.status_code // 100 == 2:
            data = response.json()
            return SaleDateUpdateResponse(
                success=True,
                reference=data.get("updateId"),
                message=data.get("message"),
            )
        return SaleDateUpdateResponse(
            success=False,
            reference=None,
            message=f"Failed with status {response.status_code}: {response.text}",
        )
