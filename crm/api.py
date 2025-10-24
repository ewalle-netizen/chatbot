"""FastAPI application exposing CRM endpoints."""
from __future__ import annotations

import uuid

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models
from .database import get_session, init_db
from .schemas import (
    ClientCreate,
    ClientRead,
    OpportunityCreate,
    OpportunityRead,
    OpportunityReport,
    SalesDashboard,
    SalesDateUpdateRead,
    SalesDateUpdateRequest,
)
from .services import CRMService

app = FastAPI(title="Infor Skyline CRM", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.post("/clients", response_model=ClientRead, status_code=201)
def create_client(payload: ClientCreate, session: Session = Depends(get_session)) -> ClientRead:
    service = CRMService(session=session)
    client = service.create_client(
        name=payload.name,
        external_id=payload.external_id,
        industry=payload.industry,
    )
    session.flush()
    return ClientRead.model_validate(client)


@app.post("/opportunities", response_model=OpportunityRead, status_code=201)
def create_opportunity(payload: OpportunityCreate, session: Session = Depends(get_session)) -> OpportunityRead:
    service = CRMService(session=session)
    try:
        client_id = uuid.UUID(payload.client_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid client id") from exc

    client = session.get(models.Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    opportunity = service.create_opportunity(
        client=client,
        name=payload.name,
        expected_close_date=payload.expected_close_date,
        amount=payload.amount,
        owner=payload.owner,
        stage=payload.stage,
        probability=payload.probability,
        infor_sales_order_id=payload.infor_sales_order_id,
    )
    session.flush()
    return OpportunityRead.model_validate(opportunity)


@app.post("/sales-dates", response_model=SalesDateUpdateRead)
def update_sales_date(payload: SalesDateUpdateRequest, session: Session = Depends(get_session)) -> SalesDateUpdateRead:
    service = CRMService(session=session)
    try:
        opportunity = service.update_sales_date(
            opportunity_id=payload.opportunity_id,
            new_date=payload.new_date,
            updated_by=payload.updated_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    session.flush()
    session.refresh(opportunity)
    updates = opportunity.sales_date_updates
    if not updates:
        raise HTTPException(status_code=500, detail="Sales date update not persisted")
    update = updates[-1]
    return SalesDateUpdateRead.model_validate(update)


@app.post("/sync/invoices", response_model=dict)
def sync_invoices(session: Session = Depends(get_session)) -> dict:
    service = CRMService(session=session)
    try:
        result = service.synchronise_invoices()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return result


@app.get("/reports/dashboard", response_model=SalesDashboard)
def dashboard(session: Session = Depends(get_session)) -> SalesDashboard:
    service = CRMService(session=session)
    return service.build_sales_dashboard()


@app.get("/reports/opportunities/{opportunity_id}", response_model=OpportunityReport)
def opportunity_report(opportunity_id: str, session: Session = Depends(get_session)) -> OpportunityReport:
    service = CRMService(session=session)
    return service.build_opportunity_report(opportunity_id=opportunity_id)
