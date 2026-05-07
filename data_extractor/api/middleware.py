from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from data_extractor.core.exceptions import DataExtractorError

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with method, path, status code, and duration."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "[%s] %s %s → %d (%.1f ms)",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response


async def domain_exception_handler(request: Request, exc: DataExtractorError) -> JSONResponse:
    """Convert unhandled domain exceptions to a structured 500 response."""
    logger.exception("Unhandled domain exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "code": "internal_error"},
    )
