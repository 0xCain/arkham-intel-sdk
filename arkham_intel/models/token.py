from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class TokenHolder(BaseModel):
    """A single holder entry from the top-holders list."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    address: Optional[str] = None
    balance: Optional[Union[str, float]] = None
    share: Optional[Union[str, float]] = None
    arkham_entity: Optional[Dict[str, Any]] = Field(None, alias="arkhamEntity")
    arkham_label: Optional[Dict[str, Any]] = Field(None, alias="arkhamLabel")


class TokenHoldersResponse(BaseModel):
    """
    Parsed response from ``GET /token/holders/{chain}/{address}``.

    ``holders`` contains the holders for the requested chain.
    ``is_complete`` indicates whether the API returned all holders or
    hit a server-side cap.
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    token_address: str = ""
    chain: str = ""
    holders: List[TokenHolder] = []
    total_holders: int = 0
    is_complete: bool = True
    warning: Optional[str] = None
    total_supply: Optional[Any] = None
    token_info: Optional[Dict[str, Any]] = None
    snapshot_time: Optional[str] = None
    raw: Dict[str, Any] = {}


class TokenMarket(BaseModel):
    """Response from ``GET /token/market/{id}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: Optional[str] = None
    name: Optional[str] = None
    symbol: Optional[str] = None
    price: Optional[float] = None
    market_cap: Optional[float] = Field(None, alias="marketCap")
    volume_24h: Optional[float] = Field(None, alias="volume24h")


class TokenPricePoint(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    timestamp: Optional[int] = None
    price: Optional[float] = None


class TokenPriceHistoryResponse(BaseModel):
    """Response from ``GET /token/price/history/{chain}/{address}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    prices: List[TokenPricePoint] = []


class TokenListItem(BaseModel):
    """A single item from ``GET /token/top`` or ``GET /token/trending``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: Optional[str] = None
    name: Optional[str] = None
    symbol: Optional[str] = None
    price: Optional[float] = None
    market_cap: Optional[float] = Field(None, alias="marketCap")
