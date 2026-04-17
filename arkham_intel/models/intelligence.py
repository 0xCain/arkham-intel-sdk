from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ArkhamEntity(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: Optional[str] = None
    type: Optional[str] = None
    id: Optional[str] = None
    website: Optional[str] = None
    twitter: Optional[str] = None


class ArkhamLabel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: Optional[str] = None
    address: Optional[str] = None
    chain: Optional[str] = None


class AddressIntelligence(BaseModel):
    """Response from ``GET /intelligence/address/{address}[/all]``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    address: Optional[str] = None
    chain: Optional[str] = None
    arkham_entity: Optional[ArkhamEntity] = Field(None, alias="arkhamEntity")
    arkham_label: Optional[ArkhamLabel] = Field(None, alias="arkhamLabel")
    is_contract: Optional[bool] = Field(None, alias="isContract")


class BatchAddressIntelligenceResponse(BaseModel):
    """Response from ``POST /intelligence/address/batch[/all]``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    addresses: Dict[str, Any] = {}


class EntityIntelligence(BaseModel):
    """Response from ``GET /intelligence/entity/{entity}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: Optional[str] = None
    type: Optional[str] = None
    id: Optional[str] = None
    website: Optional[str] = None
    twitter: Optional[str] = None


class EntitySummary(BaseModel):
    """Response from ``GET /intelligence/entity/{entity}/summary``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    entity: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None


class EntityTypesResponse(BaseModel):
    """Response from ``GET /intelligence/entity_types``."""
    entity_types: List[str] = []


class ContractInfo(BaseModel):
    """Response from ``GET /intelligence/contract/{chain}/{address}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    address: Optional[str] = None
    chain: Optional[str] = None
    name: Optional[str] = None
    is_verified: Optional[bool] = Field(None, alias="isVerified")


class SearchResult(BaseModel):
    """A single item from ``GET /intelligence/search``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    chain: Optional[str] = None
    arkham_entity: Optional[ArkhamEntity] = Field(None, alias="arkhamEntity")
    arkham_label: Optional[ArkhamLabel] = Field(None, alias="arkhamLabel")


class SearchResponse(BaseModel):
    """Response from ``GET /intelligence/search``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    results: List[SearchResult] = []
