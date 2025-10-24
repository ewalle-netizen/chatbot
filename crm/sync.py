"""Scheduling helpers for automated synchronisation tasks."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from .database import session_scope
from .services import CRMService


class SyncManager:
    """Configure scheduled jobs for invoice synchronisation and monitoring."""

    def __init__(self, *, scheduler: Optional[BackgroundScheduler] = None) -> None:
        self.scheduler = scheduler or BackgroundScheduler()

    def start(self) -> None:
        """Start the scheduler if not already running."""

        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self) -> None:
        """Stop the scheduler."""

        if self.scheduler.running:
            self.scheduler.shutdown()

    def schedule_daily_invoice_sync(self, *, hour: int = 2, minute: int = 0) -> None:
        """Register a job that pulls invoices from Infor Skyline every day."""

        self.scheduler.add_job(self._run_invoice_sync, "cron", hour=hour, minute=minute, id="invoice-sync", replace_existing=True)

    @staticmethod
    def _run_invoice_sync() -> None:
        with session_scope() as session:
            service = CRMService(session=session)
            result = service.synchronise_invoices()
            message = f"[{datetime.utcnow().isoformat()}] Synced {result['processed']} invoices"
            if result["warnings"]:
                message = f"{message} (warnings: {' | '.join(result['warnings'])})"
            print(message)
