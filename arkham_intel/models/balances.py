from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class BalanceItem(BaseModel):
    """A single token balance entry."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    token: Optional[Dict[str, Any]] = None
    chain: Optional[str] = None
    balance: Optional[Union[str, float]] = None
    usd_value: Optional[Union[str, float]] = Field(None, alias="usdValue")


class BalancesResponse(BaseModel):
    """Response from ``GET /balances/address/{address}`` or ``GET /balances/entity/{entity}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    balances: List[BalanceItem] = []
    raw: Dict[str, Any] = {}
