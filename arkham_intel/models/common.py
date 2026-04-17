from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class PaginationParams(BaseModel):
    """Common pagination parameters accepted by list endpoints."""
    limit: int = 100
    offset: int = 0


class RetryMeta(BaseModel):
    """Statistics returned alongside every API response."""
    attempts: int = 1
    rate_limited: bool = False
    rate_limit_hits: int = 0
    retry_sleep_seconds: float = 0.0


class ErrorResponse(BaseModel):
    """Represents an API-level error response."""
    error: str
    detail: Optional[str] = None


class ChainInfo(BaseModel):
    """A single chain returned by ``GET /chains``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: Optional[str] = None
    id: Optional[str] = None
