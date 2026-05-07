from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from fastapi import HTTPException, Request, status

_MAX_CALLS = 10
_PERIOD_SECONDS = 60
_log: dict[str, list[float]] = defaultdict(list)


async def check_extract_rate_limit(request: Request) -> None:
    """Sliding-window rate limit: 10 requests / 60 s per client IP."""
    key = request.client.host if request.client else "unknown"
    now = datetime.now(UTC).timestamp()
    cutoff = now - _PERIOD_SECONDS

    _log[key] = [t for t in _log[key] if t > cutoff]

    if len(_log[key]) >= _MAX_CALLS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {_MAX_CALLS} requests per {_PERIOD_SECONDS}s.",
        )

    _log[key].append(now)
