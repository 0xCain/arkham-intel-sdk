from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class PortfolioPosition(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    token: Optional[Dict[str, Any]] = None
    chain: Optional[str] = None
    balance: Optional[Union[str, float]] = None
    usd_value: Optional[Union[str, float]] = Field(None, alias="usdValue")


class PortfolioResponse(BaseModel):
    """Response from ``GET /portfolio/address/{address}`` or ``GET /portfolio/entity/{entity}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    address: Optional[str] = None
    positions: List[PortfolioPosition] = []
    total_usd_value: Optional[Union[str, float]] = Field(None, alias="totalUsdValue")
    raw: Dict[str, Any] = {}


class PortfolioTimeSeriesPoint(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    timestamp: Optional[int] = None
    usd_value: Optional[float] = Field(None, alias="usdValue")


class PortfolioTimeSeriesResponse(BaseModel):
    """Response from ``GET /portfolio/timeSeries/address/{address}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    points: List[PortfolioTimeSeriesPoint] = []
    raw: Dict[str, Any] = {}
