from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WsSessionInfo(BaseModel):
    """Parsed response from ``POST /ws/sessions`` or ``GET /ws/sessions/{id}``."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    session_id: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")
    is_connected: Optional[bool] = Field(None, alias="isConnected")
    transfers_used: Optional[int] = Field(None, alias="transfersUsed")
    raw: Dict[str, Any] = {}


class WsSubscribeMessage(BaseModel):
    """Client -> server subscribe frame."""
    id: str = "1"
    type: str = "subscribe"
    payload: Dict[str, Any] = {}


class WsTransferMessage(BaseModel):
    """A single transfer pushed via the WebSocket stream."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
