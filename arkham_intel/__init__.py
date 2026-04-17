"""
Arkham Intel Python SDK
~~~~~~~~~~~~~~~~~~~~~~~

Unofficial Python SDK for the Arkham Intelligence (Intel) API.

Basic usage::

    from arkham_intel import AsyncArkhamIntelClient

    async with AsyncArkhamIntelClient(api_key="your-api-key") as client:
        resp = await client.get_transfers(chains="bsc", tokens="0x...")
        for t in resp.transfers:
            print(t.id, t.historical_usd)
"""

__version__ = "0.2.0"

from .client import AsyncArkhamIntelClient
from .ws_client import ArkhamIntelWebSocket
from .exceptions import ArkhamApiError, ArkhamRateLimitError, ArkhamWebSocketError

__all__ = [
    "AsyncArkhamIntelClient",
    "ArkhamIntelWebSocket",
    "ArkhamApiError",
    "ArkhamRateLimitError",
    "ArkhamWebSocketError",
]
