from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class AddressInfo(BaseModel):
    """Arkham address entity that may appear in from/to fields."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    address: Optional[str] = None
    arkham_entity: Optional[Dict[str, Any]] = Field(None, alias="arkhamEntity")
    arkham_label: Optional[Dict[str, Any]] = Field(None, alias="arkhamLabel")
    chain: Optional[str] = None


class TokenAddress(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    address: Optional[str] = None
    name: Optional[str] = None
    symbol: Optional[str] = None
    chain: Optional[str] = None


class Transfer(BaseModel):
    """A single transfer record from the Arkham API."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: Optional[str] = None
    chain: Optional[Union[str, Dict[str, Any]]] = None
    transaction_hash: Optional[str] = Field(None, alias="transactionHash")
    block_number: Optional[int] = Field(None, alias="blockNumber")
    block_timestamp: Optional[str] = Field(None, alias="blockTimestamp")
    block_timestamp_ms: Optional[int] = Field(None, alias="blockTimestampMs")
    from_address: Optional[Union[AddressInfo, Dict[str, Any]]] = Field(
        None, alias="fromAddress",
    )
    to_address: Optional[Union[AddressInfo, Dict[str, Any]]] = Field(
        None, alias="toAddress",
    )
    token_address: Optional[Union[TokenAddress, Dict[str, Any], str]] = Field(
        None, alias="tokenAddress",
    )
    unit_value: Optional[Union[str, float]] = Field(None, alias="unitValue")
    historical_usd: Optional[Union[str, float]] = Field(None, alias="historicalUSD")
    token_id: Optional[str] = Field(None, alias="tokenId")
    transfer_type: Optional[str] = Field(None, alias="transferType")

    @property
    def token_address_str(self) -> str:
        if isinstance(self.token_address, dict):
            return str(self.token_address.get("address", "")).strip().lower()
        if isinstance(self.token_address, TokenAddress):
            return (self.token_address.address or "").strip().lower()
        return str(self.token_address or "").strip().lower()

    @property
    def chain_name(self) -> str:
        if isinstance(self.chain, dict):
            return str(self.chain.get("name", "")).strip().lower()
        return str(self.chain or "").strip().lower()


class TransfersResponse(BaseModel):
    """Response from ``GET /transfers``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    transfers: List[Transfer] = []


class TransactionTransfersResponse(BaseModel):
    """Response from ``GET /transfers/tx/{hash}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    transfers: List[Transfer] = []


class TransfersHistogramResponse(BaseModel):
    """Response from ``GET /transfers/histogram``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    histogram: List[Dict[str, Any]] = []
