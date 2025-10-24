"""Application configuration and settings management."""
from __future__ import annotations

from functools import lru_cache
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Central configuration for the CRM application."""

    database_url: str = Field(
        default="sqlite:///./crm.db",
        description="SQLAlchemy database URL used by the application.",
    )
    infor_base_url: str = Field(
        default="https://example.skyline.infor.com/api",
        description="Base URL for the Infor Skyline REST API.",
    )
    infor_client_id: str = Field(
        default="demo-client-id",
        description="OAuth client identifier or username for authenticating against Infor.",
    )
    infor_client_secret: str = Field(
        default="demo-client-secret",
        description="Secret used alongside the client identifier when retrieving tokens.",
    )
    infor_tenant: str = Field(
        default="tenant",
        description="Tenant or site identifier used in the Infor Skyline environment.",
    )
    infor_mock_mode: bool = Field(
        default=True,
        description=(
            "If True, the integration layer returns deterministic mock data instead of "
            "calling the remote API. Useful for development and automated tests."
        ),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached instance of :class:`Settings`."""

    return Settings()


settings = get_settings()
