from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BalanceItem(BaseModel):
    """A single token balance entry."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    token: Optional[Dict[str, Any]] = None
    chain: Optional[str] = None
    balance: Optional[Union[str, float]] = None
    usd_value: Optional[Union[str, float]] = Field(None, alias="usdValue")

    # API 有时直接返回这些字段（不嵌套在 token 里）
    name: Optional[str] = None
    symbol: Optional[str] = None
    address: Optional[str] = None
    ethereum_address: Optional[str] = Field(None, alias="ethereumAddress")


class BalancesResponse(BaseModel):
    """Response from ``GET /balances/address/{address}`` or ``GET /balances/entity/{entity}``.

    API may return ``balances`` as either:
    - a list of :class:`BalanceItem` objects, or
    - a dict keyed by chain name (e.g. ``{"bsc": [...], "ethereum": [...]}``)

    The validator normalises both forms into a flat list.
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    balances: List[BalanceItem] = []
    raw: Dict[str, Any] = {}

    @field_validator("balances", mode="before")
    @classmethod
    def _coerce_balances(cls, v: Any) -> Any:
        if v is None:
            return []
        if isinstance(v, dict):
            flat: list = []
            for chain_name, items in v.items():
                if not isinstance(items, list):
                    continue
                for item in items:
                    if isinstance(item, dict) and "chain" not in item:
                        item["chain"] = chain_name
                    flat.append(item)
            return flat
        return v
