"""
Async WebSocket client for the Arkham Intel real-time transfer stream.

Usage::

    from arkham_intel import AsyncArkhamIntelClient, ArkhamIntelWebSocket

    rest = AsyncArkhamIntelClient(api_key="your-api-key")
    ws = ArkhamIntelWebSocket(rest)

    async for transfer in ws.stream_transfers(chains=["bsc"], tokens=["0x..."]):
        print(transfer)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time as _time
from typing import Any, AsyncIterator, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

import aiohttp

from ._constants import BASE_URL, WS_CONNECT_TIMEOUT, WS_HEARTBEAT_INTERVAL
from .exceptions import ArkhamWebSocketError

logger = logging.getLogger("arkham_intel")


def _build_ws_endpoint(base_url: str, session_id: str) -> str:
    parsed = urlparse(base_url)
    ws_scheme = "wss" if parsed.scheme == "https" else "ws"
    base_ws = urlunparse((ws_scheme, parsed.netloc, "", "", "", "")).rstrip("/")
    return f"{base_ws}/ws/transfers?session_id={session_id}"


def _extract_transfers_from_payload(payload: Any) -> List[Dict[str, Any]]:
    """Best-effort extraction of transfer dicts from a WS message payload."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    if payload.get("type") == "transfer" and isinstance(payload.get("payload"), dict):
        transfer = payload["payload"].get("transfer")
        if isinstance(transfer, dict):
            return [transfer]

    for key in ("transfers", "data", "results", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict) and value.get("id"):
            return [value]

    if payload.get("id") and payload.get("transactionHash"):
        return [payload]
    if isinstance(payload.get("transfer"), dict):
        return [payload["transfer"]]
    return []


class ArkhamIntelWebSocket:
    """
    Manages the full lifecycle of an Arkham WS transfer stream:
    session creation -> connect -> subscribe -> receive.

    The class is stateless with respect to external resources (no .env
    writes, no DB). Session persistence is the caller's responsibility.
    """

    def __init__(
        self,
        rest_client: Any,
        *,
        proxy: Optional[str] = None,
        heartbeat: float = WS_HEARTBEAT_INTERVAL,
        connect_timeout: float = WS_CONNECT_TIMEOUT,
        idle_timeout: float = 60.0,
        reconnect_attempts: int = 5,
        status_poll_seconds: float = 60.0,
    ) -> None:
        self._rest = rest_client
        self._proxy = proxy or getattr(rest_client, "proxy", None)
        self._heartbeat = heartbeat
        self._connect_timeout = connect_timeout
        self._idle_timeout = idle_timeout
        self._reconnect_attempts = reconnect_attempts
        self._status_poll_seconds = status_poll_seconds

        self._session_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    @session_id.setter
    def session_id(self, value: Optional[str]) -> None:
        """Allow callers to inject a previously persisted session id."""
        self._session_id = value

    async def ensure_session(
        self,
        *,
        force_new: bool = False,
    ) -> str:
        """
        Ensure an active WS session exists, creating one if needed.

        Returns the session id.
        """
        if self._session_id and not force_new:
            try:
                info = await self._rest.get_ws_session_status(self._session_id)
                if info.is_active:
                    logger.info(
                        "Reusing WS session %s (connected=%s, used=%s)",
                        self._session_id, info.is_connected, info.transfers_used,
                    )
                    return self._session_id
                logger.info("WS session %s expired, creating new one", self._session_id)
            except Exception as exc:
                logger.warning("Session status check failed, will recreate: %s", exc)

        info = await self._rest.create_ws_session()
        if not info.session_id:
            raise ArkhamWebSocketError("WS session created but no session_id returned")
        self._session_id = info.session_id
        logger.info("Created new WS session: %s", self._session_id)
        return self._session_id

    async def stream_transfers(
        self,
        *,
        chains: Optional[List[str]] = None,
        tokens: Optional[List[str]] = None,
        filter_payload: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Yield transfer dicts as they arrive from the WebSocket.

        The method handles session creation, connection, subscription,
        and automatic reconnection.

        Parameters
        ----------
        chains : list of chain identifiers to subscribe to
        tokens : list of token addresses to subscribe to
        filter_payload : raw filter dict (overrides chains/tokens if given)
        """
        if filter_payload is None:
            filter_payload = {}
            if chains:
                filter_payload["chains"] = chains
            if tokens:
                filter_payload["tokens"] = tokens

        attempt = 0
        while True:
            try:
                session_id = await self.ensure_session()
                endpoint = _build_ws_endpoint(self._rest.base_url, session_id)
                timeout = aiohttp.ClientTimeout(total=None, connect=self._connect_timeout)

                async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as http:
                    async with http.ws_connect(
                        endpoint,
                        headers=self._rest.headers,
                        heartbeat=self._heartbeat,
                        autoping=True,
                        proxy=self._proxy,
                    ) as ws:
                        logger.info("WS connected: %s", endpoint)
                        attempt = 0

                        subscribe_msg = {
                            "id": "1",
                            "type": "subscribe",
                            "payload": {"filters": filter_payload},
                        }
                        await ws.send_json(subscribe_msg)

                        last_status = _time.monotonic()

                        while True:
                            now = _time.monotonic()
                            if now - last_status >= self._status_poll_seconds:
                                info = await self._rest.get_ws_session_status(session_id)
                                if not info.is_active:
                                    raise ArkhamWebSocketError(
                                        f"Session {session_id} became inactive"
                                    )
                                last_status = now

                            try:
                                msg = await asyncio.wait_for(
                                    ws.receive(), timeout=self._idle_timeout,
                                )
                            except asyncio.TimeoutError:
                                continue

                            if msg.type == aiohttp.WSMsgType.TEXT:
                                text = (msg.data or "").strip()
                                if not text:
                                    continue
                                try:
                                    payload = json.loads(text)
                                except Exception:
                                    logger.warning("Non-JSON WS message, skipped")
                                    continue

                                msg_type = payload.get("type") if isinstance(payload, dict) else None
                                if msg_type == "error":
                                    err = (payload.get("payload") or {})
                                    code = str(err.get("code", "")).strip()
                                    if code == "FILTER_EXISTS":
                                        continue
                                    raise ArkhamWebSocketError(f"Server error: {payload}")

                                for transfer in _extract_transfers_from_payload(payload):
                                    yield transfer

                            elif msg.type in (
                                aiohttp.WSMsgType.CLOSE,
                                aiohttp.WSMsgType.CLOSED,
                            ):
                                raise ArkhamWebSocketError("WS connection closed")
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                raise ArkhamWebSocketError(f"WS error: {ws.exception()}")

            except (asyncio.CancelledError, GeneratorExit):
                return

            except Exception as exc:
                attempt += 1
                logger.warning("WS stream error (attempt %d): %s", attempt, exc)
                if attempt >= self._reconnect_attempts:
                    attempt = 0
                    self._session_id = None
                await asyncio.sleep(1.5)

    async def close(self) -> None:
        """Discard any cached session state."""
        self._session_id = None
