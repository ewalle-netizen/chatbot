"""Entry point to run the FastAPI CRM server."""
from __future__ import annotations

import uvicorn

from crm.api import app


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
