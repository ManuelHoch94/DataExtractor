from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import data_extractor
from data_extractor.api.middleware import RequestLoggingMiddleware, domain_exception_handler
from data_extractor.api.routers import extraction, health, schemas
from data_extractor.core.exceptions import DataExtractorError

logger = logging.getLogger(__name__)

_API_PREFIX = "/api/v1"

_DESCRIPTION = """
## DataExtractor API

Extract structured data from PDF documents using AI-powered field mapping.

### How it works
1. Upload a PDF via `POST /api/v1/extract`
2. Provide a **schema definition** – a JSON object mapping field names to extraction hints
3. Receive extracted fields with confidence scores, ready for index ingestion

### Provider
The active LLM provider (OpenAI / Anthropic / internal) is configured via environment
variables and visible on the `GET /api/v1/health` endpoint.
"""


def create_app(*, cors_origins: list[str] | None = None) -> FastAPI:
    """Factory function – create and configure the FastAPI application.

    Args:
        cors_origins: Allowed CORS origins. Defaults to ``["*"]`` (dev-friendly).
                      Override in production to restrict origins.

    Returns:
        A fully configured :class:`FastAPI` instance.
    """
    app = FastAPI(
        title="DataExtractor API",
        description=_DESCRIPTION,
        version=data_extractor.__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "Manuel Hochreiter",
            "url": "https://github.com/ManuelHoch94/DataExtractor",
        },
        license_info={"name": "MIT"},
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Domain exception handler
    app.add_exception_handler(DataExtractorError, domain_exception_handler)

    # Routers
    app.include_router(health.router, prefix=_API_PREFIX)
    app.include_router(schemas.router, prefix=_API_PREFIX)
    app.include_router(extraction.router, prefix=_API_PREFIX)

    @app.get("/", include_in_schema=False)
    def root():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/docs")

    return app
