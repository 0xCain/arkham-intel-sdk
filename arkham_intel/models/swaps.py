from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Swap(BaseModel):
    """A single DEX swap record."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: Optional[str] = None
    chain: Optional[str] = None
    transaction_hash: Optional[str] = Field(None, alias="transactionHash")
    block_timestamp: Optional[str] = Field(None, alias="blockTimestamp")
    block_timestamp_ms: Optional[int] = Field(None, alias="blockTimestampMs")
    maker_address: Optional[Dict[str, Any]] = Field(None, alias="makerAddress")
    token_in: Optional[Dict[str, Any]] = Field(None, alias="tokenIn")
    token_out: Optional[Dict[str, Any]] = Field(None, alias="tokenOut")
    amount_in: Optional[Union[str, float]] = Field(None, alias="amountIn")
    amount_out: Optional[Union[str, float]] = Field(None, alias="amountOut")
    usd_value: Optional[Union[str, float]] = Field(None, alias="usdValue")


class SwapsResponse(BaseModel):
    """Response from ``GET /swaps``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    swaps: List[Swap] = []
