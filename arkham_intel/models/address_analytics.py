"""Models for counterparties, flow, history and volume endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


# -- Counterparties --------------------------------------------------------

class Counterparty(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    address: Optional[str] = None
    arkham_entity: Optional[Dict[str, Any]] = Field(None, alias="arkhamEntity")
    arkham_label: Optional[Dict[str, Any]] = Field(None, alias="arkhamLabel")
    transfer_count: Optional[int] = Field(None, alias="transferCount")
    usd_value: Optional[Union[str, float]] = Field(None, alias="usdValue")


class CounterpartiesResponse(BaseModel):
    """Response from ``GET /counterparties/address/{address}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    counterparties: List[Counterparty] = []
    raw: Dict[str, Any] = {}


# -- Flow ------------------------------------------------------------------

class FlowPoint(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    timestamp: Optional[int] = None
    inflow_usd: Optional[float] = Field(None, alias="inflowUsd")
    outflow_usd: Optional[float] = Field(None, alias="outflowUsd")


class FlowResponse(BaseModel):
    """Response from ``GET /flow/address/{address}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    flow: List[FlowPoint] = []
    raw: Dict[str, Any] = {}


# -- History ---------------------------------------------------------------

class HistoryResponse(BaseModel):
    """Response from ``GET /history/address/{address}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    history: List[Dict[str, Any]] = []
    raw: Dict[str, Any] = {}


# -- Volume ----------------------------------------------------------------

class VolumeResponse(BaseModel):
    """Response from ``GET /volume/address/{address}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    volume: List[Dict[str, Any]] = []
    raw: Dict[str, Any] = {}


# -- Transaction details ---------------------------------------------------

class TransactionDetail(BaseModel):
    """Response from ``GET /tx/{hash}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    transaction_hash: Optional[str] = Field(None, alias="transactionHash")
    chain: Optional[str] = None
    block_number: Optional[int] = Field(None, alias="blockNumber")
    block_timestamp: Optional[str] = Field(None, alias="blockTimestamp")
    from_address: Optional[Dict[str, Any]] = Field(None, alias="fromAddress")
    to_address: Optional[Dict[str, Any]] = Field(None, alias="toAddress")
    value: Optional[Union[str, float]] = None
    gas_used: Optional[int] = Field(None, alias="gasUsed")
    raw: Dict[str, Any] = {}
