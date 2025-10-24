"""Pydantic schemas for requests and responses."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .models import InvoiceStatus, OpportunityStage


class ClientCreate(BaseModel):
    name: str
    external_id: Optional[str] = None
    industry: Optional[str] = None


class ClientRead(BaseModel):
    id: str
    name: str
    external_id: Optional[str]
    industry: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OpportunityCreate(BaseModel):
    client_id: str
    name: str
    amount: float = Field(ge=0)
    expected_close_date: Optional[date] = None
    owner: Optional[str] = None
    stage: OpportunityStage = OpportunityStage.prospect
    probability: float = Field(default=0, ge=0, le=100)
    infor_sales_order_id: Optional[str] = None


class OpportunityRead(BaseModel):
    id: str
    client_id: str
    name: str
    stage: OpportunityStage
    probability: float
    expected_close_date: Optional[date]
    actual_close_date: Optional[date]
    amount: float
    owner: Optional[str]
    infor_sales_order_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalesDateUpdateRequest(BaseModel):
    opportunity_id: str
    new_date: date
    updated_by: str


class SalesDateUpdateRead(BaseModel):
    id: str
    opportunity_id: str
    previous_date: Optional[date]
    new_date: date
    updated_by: str
    updated_at: datetime
    synced_with_infor: bool
    sync_reference: Optional[str]

    class Config:
        from_attributes = True


class InvoiceRead(BaseModel):
    id: str
    opportunity_id: str
    external_id: Optional[str]
    amount: float
    issue_date: date
    due_date: Optional[date]
    status: InvoiceStatus
    currency: str
    last_sync_at: Optional[datetime]

    class Config:
        from_attributes = True


class OpportunityReport(BaseModel):
    opportunity: OpportunityRead
    invoices: List[InvoiceRead]


class SalesDashboard(BaseModel):
    total_open_pipeline: float
    total_invoiced: float
    total_paid: float
    overdue_invoices: int
