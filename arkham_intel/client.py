"""
Async REST client for the Arkham Intel API.

Usage::

    from arkham_intel import AsyncArkhamIntelClient

    async with AsyncArkhamIntelClient(api_key="key") as client:
        resp = await client.get_transfers(chains="bsc", tokens="0x...")
        for t in resp.transfers:
            print(t.id, t.historical_usd)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

import httpx

from ._constants import (
    BASE_URL,
    CHAIN_NAME_MAP,
    DEFAULT_LONG_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_RETRY_DELAY,
    DEFAULT_TIMEOUT,
)
from ._retry import request_with_retry
from .exceptions import ArkhamApiError
from .models.address_analytics import (
    CounterpartiesResponse,
    FlowResponse,
    HistoryResponse,
    TransactionDetail,
    VolumeResponse,
)
from .models.balances import BalancesResponse
from .models.common import ChainInfo
from .models.intelligence import (
    AddressIntelligence,
    BatchAddressIntelligenceResponse,
    ContractInfo,
    EntityIntelligence,
    EntitySummary,
    EntityTypesResponse,
    SearchResponse,
)
from .models.portfolio import PortfolioResponse, PortfolioTimeSeriesResponse
from .models.swaps import SwapsResponse
from .models.token import (
    TokenHolder,
    TokenHoldersResponse,
    TokenMarket,
    TokenPriceHistoryResponse,
)
from .models.transfers import (
    TransfersHistogramResponse,
    TransfersResponse,
    TransactionTransfersResponse,
)
from .models.websocket import WsSessionInfo

logger = logging.getLogger("arkham_intel")


def _normalize_chain(chain: str) -> str:
    key = str(chain).strip().lower()
    return CHAIN_NAME_MAP.get(key, key)


def _serialize_filter_values(value: Union[str, List[str], None]) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        parts = [str(v).strip() for v in value if str(v).strip()]
        return ",".join(parts)
    return str(value).strip()


class AsyncArkhamIntelClient:
    """
    Async HTTP client for the Arkham Intelligence (Intel) API.

    Supports ``async with`` for efficient connection reuse::

        async with AsyncArkhamIntelClient(api_key="...") as client:
            ...

    If used without a context manager the client is still usable — a
    transient ``httpx.AsyncClient`` is created per request.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        max_retry_delay: float = DEFAULT_MAX_RETRY_DELAY,
        proxy: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_retry_delay = max_retry_delay
        self.proxy = proxy
        self.headers: Dict[str, str] = {
            "API-Key": self.api_key,
            "Accept": "application/json",
        }
        self._shared_client: Optional[httpx.AsyncClient] = None
        self._owns_client: bool = False

    # ------------------------------------------------------------------
    # Async context manager — shared httpx.AsyncClient
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "AsyncArkhamIntelClient":
        self._shared_client = httpx.AsyncClient(
            timeout=self.timeout,
            proxy=self.proxy,
        )
        self._owns_client = True
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._shared_client and self._owns_client:
            await self._shared_client.aclose()
            self._shared_client = None
            self._owns_client = False

    async def aclose(self) -> None:
        """Explicitly close the shared HTTP client (if any)."""
        await self.__aexit__(None, None, None)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_client(self, timeout: Optional[float] = None) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=timeout or self.timeout,
            proxy=self.proxy,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        label: str = "",
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Core request method.  Always uses ``request_with_retry`` so that
        *every* endpoint gets consistent retry / Retry-After handling.
        """
        url = f"{self.base_url}{path}"

        if self._shared_client is not None:
            data, _meta = await request_with_retry(
                self._shared_client,
                method,
                url,
                label=label or path,
                max_retries=self.max_retries,
                max_delay=self.max_retry_delay,
                headers=self.headers,
                **kwargs,
            )
            return data

        async with self._make_client(timeout) as client:
            data, _meta = await request_with_retry(
                client,
                method,
                url,
                label=label or path,
                max_retries=self.max_retries,
                max_delay=self.max_retry_delay,
                headers=self.headers,
                **kwargs,
            )
            return data

    async def _request_with_meta(
        self,
        method: str,
        path: str,
        *,
        label: str = "",
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> tuple[Any, Dict[str, Any]]:
        url = f"{self.base_url}{path}"

        if self._shared_client is not None:
            return await request_with_retry(
                self._shared_client,
                method,
                url,
                label=label or path,
                max_retries=self.max_retries,
                max_delay=self.max_retry_delay,
                headers=self.headers,
                **kwargs,
            )

        async with self._make_client(timeout) as client:
            return await request_with_retry(
                client,
                method,
                url,
                label=label or path,
                max_retries=self.max_retries,
                max_delay=self.max_retry_delay,
                headers=self.headers,
                **kwargs,
            )

    # ==================================================================
    # Chains
    # ==================================================================

    async def get_chains(self) -> List[ChainInfo]:
        """
        List all chains supported by Arkham.

        ``GET /chains``
        """
        data = await self._request("GET", "/chains", label="/chains")
        if isinstance(data, list):
            return [ChainInfo.model_validate(item) for item in data]
        return []

    # ==================================================================
    # Transfer endpoints
    # ==================================================================

    async def get_transfers(
        self,
        *,
        base: Optional[str] = None,
        chains: Optional[str] = None,
        tokens: Optional[str] = None,
        from_address: Union[str, List[str], None] = None,
        to_address: Union[str, List[str], None] = None,
        flow: Optional[str] = None,
        counterparties: Optional[str] = None,
        time_gte: Union[int, str, None] = None,
        time_lte: Union[int, str, None] = None,
        time_last: Optional[str] = None,
        value_gte: Optional[float] = None,
        value_lte: Optional[float] = None,
        usd_gte: Optional[float] = None,
        usd_lte: Optional[float] = None,
        sort_key: Optional[str] = None,
        sort_dir: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TransfersResponse:
        """
        Query transfers.

        ``GET /transfers``
        """
        params: Dict[str, Any] = {}
        if base:
            params["base"] = base
        if chains:
            params["chains"] = chains
        if tokens:
            params["tokens"] = tokens
        ser_from = _serialize_filter_values(from_address)
        ser_to = _serialize_filter_values(to_address)
        if ser_from:
            params["from"] = ser_from
        if ser_to:
            params["to"] = ser_to
        if flow:
            params["flow"] = flow
        if counterparties:
            params["counterparties"] = counterparties
        if time_gte is not None:
            params["timeGte"] = str(time_gte)
        if time_lte is not None:
            params["timeLte"] = str(time_lte)
        if time_last:
            params["timeLast"] = time_last
        if value_gte is not None:
            params["valueGte"] = str(value_gte)
        if value_lte is not None:
            params["valueLte"] = str(value_lte)
        if usd_gte is not None:
            params["usdGte"] = str(usd_gte)
        if usd_lte is not None:
            params["usdLte"] = str(usd_lte)
        if sort_key:
            params["sortKey"] = sort_key
        if sort_dir:
            params["sortDir"] = sort_dir
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset

        data = await self._request(
            "GET", "/transfers",
            label="/transfers",
            timeout=DEFAULT_LONG_TIMEOUT,
            params=params,
        )
        if isinstance(data, dict):
            return TransfersResponse.model_validate(data)
        return TransfersResponse()

    async def get_transaction_transfers(
        self,
        tx_hash: str,
        *,
        chain: str = "bsc",
        transfer_type: str = "token",
    ) -> TransactionTransfersResponse:
        """
        Get all transfer events for a single transaction.

        ``GET /transfers/tx/{hash}``
        """
        arkham_chain = _normalize_chain(chain)
        params: Dict[str, str] = {"chain": arkham_chain, "transferType": transfer_type}
        data = await self._request(
            "GET",
            f"/transfers/tx/{tx_hash}",
            label=f"/transfers/tx/{tx_hash}",
            params=params,
        )
        if isinstance(data, list):
            return TransactionTransfersResponse(transfers=data)
        if isinstance(data, dict):
            return TransactionTransfersResponse.model_validate(data)
        return TransactionTransfersResponse()

    async def get_transfers_histogram(
        self,
        *,
        chains: Optional[str] = None,
        tokens: Optional[str] = None,
        from_address: Union[str, List[str], None] = None,
        to_address: Union[str, List[str], None] = None,
        time_gte: Union[int, str, None] = None,
        time_lte: Union[int, str, None] = None,
        time_last: Optional[str] = None,
    ) -> TransfersHistogramResponse:
        """
        Transfer histogram data.

        ``GET /transfers/histogram``
        """
        params: Dict[str, Any] = {}
        if chains:
            params["chains"] = chains
        if tokens:
            params["tokens"] = tokens
        ser_from = _serialize_filter_values(from_address)
        ser_to = _serialize_filter_values(to_address)
        if ser_from:
            params["from"] = ser_from
        if ser_to:
            params["to"] = ser_to
        if time_gte is not None:
            params["timeGte"] = str(time_gte)
        if time_lte is not None:
            params["timeLte"] = str(time_lte)
        if time_last:
            params["timeLast"] = time_last
        data = await self._request(
            "GET", "/transfers/histogram",
            label="/transfers/histogram",
            params=params,
        )
        if isinstance(data, dict):
            return TransfersHistogramResponse.model_validate(data)
        return TransfersHistogramResponse()

    async def get_transaction(
        self,
        tx_hash: str,
        *,
        chain: Optional[str] = None,
    ) -> TransactionDetail:
        """
        Get transaction details.

        ``GET /tx/{hash}``
        """
        params: Dict[str, str] = {}
        if chain:
            params["chain"] = _normalize_chain(chain)
        data = await self._request(
            "GET",
            f"/tx/{tx_hash}",
            label=f"/tx/{tx_hash}",
            params=params,
        )
        if isinstance(data, dict):
            obj = TransactionDetail.model_validate(data)
            obj.raw = data
            return obj
        return TransactionDetail()

    # ==================================================================
    # Token endpoints
    # ==================================================================

    async def get_token_holders_snapshot(
        self,
        chain: str,
        token_address: str,
        *,
        group_by_entity: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> TokenHoldersResponse:
        """
        Get the top token holders snapshot.

        ``GET /token/holders/{chain}/{address}``
        """
        arkham_chain = _normalize_chain(chain)
        params: Dict[str, Any] = {}
        if group_by_entity is not None:
            params["groupByEntity"] = str(group_by_entity).lower()
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        data = await self._request(
            "GET",
            f"/token/holders/{arkham_chain}/{token_address}",
            label=f"/token/holders/{arkham_chain}/{token_address}",
            params=params or None,
        )
        if not isinstance(data, dict):
            return TokenHoldersResponse(token_address=token_address, chain=chain)

        address_top_holders = data.get("addressTopHolders", {})
        holders_list: List[Dict[str, Any]] = []
        if isinstance(address_top_holders, dict):
            holders_list = address_top_holders.get(arkham_chain, [])

        is_complete = True
        warning = None
        if len(holders_list) in (100, 250, 500, 1000):
            is_complete = False
            warning = (
                f"API returned {len(holders_list)} holders — "
                "this may be a server-side cap; actual count could be higher."
            )

        total_supply = data.get("totalSupply")
        if isinstance(total_supply, dict):
            total_supply = total_supply.get(arkham_chain, 0)

        holders = [TokenHolder.model_validate(h) for h in holders_list]

        return TokenHoldersResponse(
            token_address=token_address,
            chain=chain,
            holders=holders,
            total_holders=len(holders),
            is_complete=is_complete,
            warning=warning,
            total_supply=total_supply,
            token_info=data.get("token"),
            snapshot_time=data.get("timestamp"),
            raw=data,
        )

    async def get_token_market(self, token_id: str) -> TokenMarket:
        """
        Token market data.

        ``GET /token/market/{id}``
        """
        data = await self._request(
            "GET",
            f"/token/market/{token_id}",
            label=f"/token/market/{token_id}",
        )
        if isinstance(data, dict):
            return TokenMarket.model_validate(data)
        return TokenMarket()

    async def get_token_price_history(
        self,
        chain: str,
        address: str,
    ) -> TokenPriceHistoryResponse:
        """
        Historical price data for a token.

        ``GET /token/price/history/{chain}/{address}``
        """
        arkham_chain = _normalize_chain(chain)
        data = await self._request(
            "GET",
            f"/token/price/history/{arkham_chain}/{address}",
            label=f"/token/price/history/{arkham_chain}/{address}",
        )
        if isinstance(data, dict):
            return TokenPriceHistoryResponse.model_validate(data)
        if isinstance(data, list):
            return TokenPriceHistoryResponse(prices=data)
        return TokenPriceHistoryResponse()

    async def get_token_top(self) -> List[Dict[str, Any]]:
        """
        Top tokens by market cap.

        ``GET /token/top``
        """
        data = await self._request("GET", "/token/top", label="/token/top")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("tokens", [])
        return []

    async def get_token_trending(self) -> List[Dict[str, Any]]:
        """
        Trending tokens.

        ``GET /token/trending``
        """
        data = await self._request("GET", "/token/trending", label="/token/trending")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("tokens", [])
        return []

    # ==================================================================
    # Intelligence endpoints
    # ==================================================================

    async def get_address_intelligence(
        self,
        address: str,
        *,
        chain: Optional[str] = None,
    ) -> AddressIntelligence:
        """
        Get intelligence for an address.

        Without *chain*: ``GET /intelligence/address/{address}/all`` (cross-chain).
        With *chain*: ``GET /intelligence/address/{address}?chain=...`` (single chain).
        """
        if chain:
            params: Dict[str, str] = {"chain": _normalize_chain(chain)}
            data = await self._request(
                "GET",
                f"/intelligence/address/{address}",
                label=f"intelligence/address/{address}",
                params=params,
            )
        else:
            data = await self._request(
                "GET",
                f"/intelligence/address/{address}/all",
                label=f"intelligence/address/{address}/all",
            )
        if isinstance(data, dict):
            return AddressIntelligence.model_validate(data)
        return AddressIntelligence(address=address)

    async def get_address_intelligence_batch(
        self,
        addresses: List[str],
        *,
        chain: Optional[str] = None,
    ) -> BatchAddressIntelligenceResponse:
        """
        Single-chain batch intelligence.

        ``POST /intelligence/address/batch``
        """
        cleaned = _dedupe_addresses(addresses)
        if not cleaned:
            return BatchAddressIntelligenceResponse()

        params: Dict[str, str] = {}
        if chain:
            params["chain"] = _normalize_chain(chain)

        data = await self._request(
            "POST",
            "/intelligence/address/batch",
            label="intelligence/address/batch",
            timeout=DEFAULT_LONG_TIMEOUT,
            params=params,
            json={"addresses": cleaned},
        )
        return _parse_batch_intel_response(data)

    async def get_address_intelligence_batch_all(
        self,
        addresses: List[str],
        *,
        chain: Optional[str] = None,
    ) -> BatchAddressIntelligenceResponse:
        """
        Cross-chain batch intelligence for up to 1 000 addresses.

        ``POST /intelligence/address/batch/all``
        """
        cleaned = _dedupe_addresses(addresses)
        if not cleaned:
            return BatchAddressIntelligenceResponse()

        params: Dict[str, str] = {}
        if chain:
            params["chain"] = _normalize_chain(chain)

        data = await self._request(
            "POST",
            "/intelligence/address/batch/all",
            label="intelligence/address/batch/all",
            timeout=DEFAULT_LONG_TIMEOUT,
            params=params,
            json={"addresses": cleaned},
        )
        return _parse_batch_intel_response(data)

    async def get_entity_intelligence(self, entity: str) -> EntityIntelligence:
        """
        Entity intelligence.

        ``GET /intelligence/entity/{entity}``
        """
        data = await self._request(
            "GET",
            f"/intelligence/entity/{entity}",
            label=f"intelligence/entity/{entity}",
        )
        if isinstance(data, dict):
            return EntityIntelligence.model_validate(data)
        return EntityIntelligence()

    async def get_entity_summary(self, entity: str) -> EntitySummary:
        """
        Entity summary.

        ``GET /intelligence/entity/{entity}/summary``
        """
        data = await self._request(
            "GET",
            f"/intelligence/entity/{entity}/summary",
            label=f"intelligence/entity/{entity}/summary",
        )
        if isinstance(data, dict):
            return EntitySummary.model_validate(data)
        return EntitySummary()

    async def get_entity_types(self) -> EntityTypesResponse:
        """
        List all known entity types.

        ``GET /intelligence/entity_types``
        """
        data = await self._request(
            "GET",
            "/intelligence/entity_types",
            label="/intelligence/entity_types",
        )
        if isinstance(data, list):
            types = sorted({
                str(item).strip().lower()
                for item in data
                if str(item).strip()
            })
            return EntityTypesResponse(entity_types=types)
        return EntityTypesResponse()

    async def get_contract_info(self, chain: str, address: str) -> ContractInfo:
        """
        Get contract metadata.

        ``GET /intelligence/contract/{chain}/{address}``
        """
        arkham_chain = _normalize_chain(chain)
        data = await self._request(
            "GET",
            f"/intelligence/contract/{arkham_chain}/{address}",
            label=f"/intelligence/contract/{arkham_chain}/{address}",
        )
        if isinstance(data, dict):
            return ContractInfo.model_validate(data)
        return ContractInfo(address=address, chain=chain)

    async def search(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
    ) -> SearchResponse:
        """
        Search addresses, entities, and tokens.

        ``GET /intelligence/search``
        """
        params: Dict[str, Any] = {"q": query}
        if limit is not None:
            params["limit"] = limit
        data = await self._request(
            "GET",
            "/intelligence/search",
            label="/intelligence/search",
            params=params,
        )
        if isinstance(data, dict):
            return SearchResponse.model_validate(data)
        if isinstance(data, list):
            return SearchResponse(results=data)
        return SearchResponse()

    # ==================================================================
    # Balances endpoints
    # ==================================================================

    async def get_address_balances(
        self,
        address: str,
        *,
        chains: Optional[str] = None,
    ) -> BalancesResponse:
        """
        Token balances for an address.

        ``GET /balances/address/{address}``
        """
        params: Dict[str, str] = {}
        if chains:
            params["chains"] = chains
        data = await self._request(
            "GET",
            f"/balances/address/{address}",
            label=f"/balances/address/{address}",
            params=params or None,
        )
        return _parse_balances(data)

    async def get_entity_balances(
        self,
        entity: str,
        *,
        chains: Optional[str] = None,
    ) -> BalancesResponse:
        """
        Token balances for an entity.

        ``GET /balances/entity/{entity}``
        """
        params: Dict[str, str] = {}
        if chains:
            params["chains"] = chains
        data = await self._request(
            "GET",
            f"/balances/entity/{entity}",
            label=f"/balances/entity/{entity}",
            params=params or None,
        )
        return _parse_balances(data)

    # ==================================================================
    # Portfolio endpoints
    # ==================================================================

    async def get_portfolio(
        self,
        address: str,
        *,
        time: Optional[int] = None,
        chains: Optional[str] = None,
    ) -> PortfolioResponse:
        """
        Address portfolio.

        ``GET /portfolio/address/{address}``
        """
        params: Dict[str, Any] = {}
        if time is not None:
            params["time"] = time
        if chains:
            params["chains"] = chains
        data = await self._request(
            "GET",
            f"/portfolio/address/{address}",
            label=f"/portfolio/address/{address}",
            params=params or None,
        )
        if isinstance(data, dict):
            obj = PortfolioResponse.model_validate(data)
            obj.raw = data
            return obj
        return PortfolioResponse(address=address)

    async def get_entity_portfolio(
        self,
        entity: str,
        *,
        time: Optional[int] = None,
        chains: Optional[str] = None,
    ) -> PortfolioResponse:
        """
        Entity portfolio.

        ``GET /portfolio/entity/{entity}``
        """
        params: Dict[str, Any] = {}
        if time is not None:
            params["time"] = time
        if chains:
            params["chains"] = chains
        data = await self._request(
            "GET",
            f"/portfolio/entity/{entity}",
            label=f"/portfolio/entity/{entity}",
            params=params or None,
        )
        if isinstance(data, dict):
            obj = PortfolioResponse.model_validate(data)
            obj.raw = data
            return obj
        return PortfolioResponse()

    async def get_portfolio_time_series(
        self,
        address: str,
        *,
        time_gte: Union[int, str, None] = None,
        time_lte: Union[int, str, None] = None,
    ) -> PortfolioTimeSeriesResponse:
        """
        Portfolio time-series data.

        ``GET /portfolio/timeSeries/address/{address}``
        """
        params: Dict[str, Any] = {}
        if time_gte is not None:
            params["timeGte"] = str(time_gte)
        if time_lte is not None:
            params["timeLte"] = str(time_lte)
        data = await self._request(
            "GET",
            f"/portfolio/timeSeries/address/{address}",
            label=f"/portfolio/timeSeries/address/{address}",
            params=params or None,
        )
        if isinstance(data, dict):
            return PortfolioTimeSeriesResponse.model_validate(data)
        return PortfolioTimeSeriesResponse()

    # ==================================================================
    # Swaps
    # ==================================================================

    async def get_swaps(
        self,
        *,
        chains: Optional[str] = None,
        tokens: Optional[str] = None,
        from_address: Union[str, List[str], None] = None,
        to_address: Union[str, List[str], None] = None,
        time_gte: Union[int, str, None] = None,
        time_lte: Union[int, str, None] = None,
        time_last: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SwapsResponse:
        """
        DEX swaps.

        ``GET /swaps``
        """
        params: Dict[str, Any] = {}
        if chains:
            params["chains"] = chains
        if tokens:
            params["tokens"] = tokens
        ser_from = _serialize_filter_values(from_address)
        ser_to = _serialize_filter_values(to_address)
        if ser_from:
            params["from"] = ser_from
        if ser_to:
            params["to"] = ser_to
        if time_gte is not None:
            params["timeGte"] = str(time_gte)
        if time_lte is not None:
            params["timeLte"] = str(time_lte)
        if time_last:
            params["timeLast"] = time_last
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        data = await self._request(
            "GET", "/swaps",
            label="/swaps",
            timeout=DEFAULT_LONG_TIMEOUT,
            params=params,
        )
        if isinstance(data, dict):
            return SwapsResponse.model_validate(data)
        return SwapsResponse()

    # ==================================================================
    # Counterparties
    # ==================================================================

    async def get_address_counterparties(
        self,
        address: str,
        *,
        chains: Optional[str] = None,
        time_gte: Union[int, str, None] = None,
        time_lte: Union[int, str, None] = None,
        time_last: Optional[str] = None,
    ) -> CounterpartiesResponse:
        """``GET /counterparties/address/{address}``"""
        params: Dict[str, Any] = {}
        if chains:
            params["chains"] = chains
        if time_gte is not None:
            params["timeGte"] = str(time_gte)
        if time_lte is not None:
            params["timeLte"] = str(time_lte)
        if time_last:
            params["timeLast"] = time_last
        data = await self._request(
            "GET",
            f"/counterparties/address/{address}",
            label=f"/counterparties/address/{address}",
            params=params or None,
        )
        if isinstance(data, dict):
            obj = CounterpartiesResponse.model_validate(data)
            obj.raw = data
            return obj
        return CounterpartiesResponse()

    async def get_entity_counterparties(
        self,
        entity: str,
        *,
        chains: Optional[str] = None,
        time_gte: Union[int, str, None] = None,
        time_lte: Union[int, str, None] = None,
        time_last: Optional[str] = None,
    ) -> CounterpartiesResponse:
        """``GET /counterparties/entity/{entity}``"""
        params: Dict[str, Any] = {}
        if chains:
            params["chains"] = chains
        if time_gte is not None:
            params["timeGte"] = str(time_gte)
        if time_lte is not None:
            params["timeLte"] = str(time_lte)
        if time_last:
            params["timeLast"] = time_last
        data = await self._request(
            "GET",
            f"/counterparties/entity/{entity}",
            label=f"/counterparties/entity/{entity}",
            params=params or None,
        )
        if isinstance(data, dict):
            obj = CounterpartiesResponse.model_validate(data)
            obj.raw = data
            return obj
        return CounterpartiesResponse()

    # ==================================================================
    # Flow
    # ==================================================================

    async def get_address_flow(
        self,
        address: str,
        *,
        chains: Optional[str] = None,
        time_gte: Union[int, str, None] = None,
        time_lte: Union[int, str, None] = None,
        time_last: Optional[str] = None,
    ) -> FlowResponse:
        """``GET /flow/address/{address}``"""
        params: Dict[str, Any] = {}
        if chains:
            params["chains"] = chains
        if time_gte is not None:
            params["timeGte"] = str(time_gte)
        if time_lte is not None:
            params["timeLte"] = str(time_lte)
        if time_last:
            params["timeLast"] = time_last
        data = await self._request(
            "GET",
            f"/flow/address/{address}",
            label=f"/flow/address/{address}",
            params=params or None,
        )
        if isinstance(data, dict):
            obj = FlowResponse.model_validate(data)
            obj.raw = data
            return obj
        return FlowResponse()

    async def get_entity_flow(
        self,
        entity: str,
        *,
        chains: Optional[str] = None,
        time_gte: Union[int, str, None] = None,
        time_lte: Union[int, str, None] = None,
        time_last: Optional[str] = None,
    ) -> FlowResponse:
        """``GET /flow/entity/{entity}``"""
        params: Dict[str, Any] = {}
        if chains:
            params["chains"] = chains
        if time_gte is not None:
            params["timeGte"] = str(time_gte)
        if time_lte is not None:
            params["timeLte"] = str(time_lte)
        if time_last:
            params["timeLast"] = time_last
        data = await self._request(
            "GET",
            f"/flow/entity/{entity}",
            label=f"/flow/entity/{entity}",
            params=params or None,
        )
        if isinstance(data, dict):
            obj = FlowResponse.model_validate(data)
            obj.raw = data
            return obj
        return FlowResponse()

    # ==================================================================
    # History
    # ==================================================================

    async def get_address_history(
        self,
        address: str,
        *,
        chains: Optional[str] = None,
    ) -> HistoryResponse:
        """``GET /history/address/{address}``"""
        params: Dict[str, str] = {}
        if chains:
            params["chains"] = chains
        data = await self._request(
            "GET",
            f"/history/address/{address}",
            label=f"/history/address/{address}",
            params=params or None,
        )
        if isinstance(data, dict):
            obj = HistoryResponse.model_validate(data)
            obj.raw = data
            return obj
        return HistoryResponse()

    async def get_entity_history(
        self,
        entity: str,
        *,
        chains: Optional[str] = None,
    ) -> HistoryResponse:
        """``GET /history/entity/{entity}``"""
        params: Dict[str, str] = {}
        if chains:
            params["chains"] = chains
        data = await self._request(
            "GET",
            f"/history/entity/{entity}",
            label=f"/history/entity/{entity}",
            params=params or None,
        )
        if isinstance(data, dict):
            obj = HistoryResponse.model_validate(data)
            obj.raw = data
            return obj
        return HistoryResponse()

    # ==================================================================
    # Volume
    # ==================================================================

    async def get_address_volume(
        self,
        address: str,
        *,
        chains: Optional[str] = None,
        time_gte: Union[int, str, None] = None,
        time_lte: Union[int, str, None] = None,
        time_last: Optional[str] = None,
    ) -> VolumeResponse:
        """``GET /volume/address/{address}``"""
        params: Dict[str, Any] = {}
        if chains:
            params["chains"] = chains
        if time_gte is not None:
            params["timeGte"] = str(time_gte)
        if time_lte is not None:
            params["timeLte"] = str(time_lte)
        if time_last:
            params["timeLast"] = time_last
        data = await self._request(
            "GET",
            f"/volume/address/{address}",
            label=f"/volume/address/{address}",
            params=params or None,
        )
        if isinstance(data, dict):
            obj = VolumeResponse.model_validate(data)
            obj.raw = data
            return obj
        return VolumeResponse()

    async def get_entity_volume(
        self,
        entity: str,
        *,
        chains: Optional[str] = None,
        time_gte: Union[int, str, None] = None,
        time_lte: Union[int, str, None] = None,
        time_last: Optional[str] = None,
    ) -> VolumeResponse:
        """``GET /volume/entity/{entity}``"""
        params: Dict[str, Any] = {}
        if chains:
            params["chains"] = chains
        if time_gte is not None:
            params["timeGte"] = str(time_gte)
        if time_lte is not None:
            params["timeLte"] = str(time_lte)
        if time_last:
            params["timeLast"] = time_last
        data = await self._request(
            "GET",
            f"/volume/entity/{entity}",
            label=f"/volume/entity/{entity}",
            params=params or None,
        )
        if isinstance(data, dict):
            obj = VolumeResponse.model_validate(data)
            obj.raw = data
            return obj
        return VolumeResponse()

    # ==================================================================
    # WebSocket session management (REST part)
    # ==================================================================

    async def create_ws_session(self) -> WsSessionInfo:
        """
        Create a new WebSocket session (v1, deprecated).

        ``POST /ws/sessions``

        .. deprecated::
            Arkham recommends using WebSocket v2 endpoints instead.
        """
        data = await self._request(
            "POST",
            "/ws/sessions",
            label="/ws/sessions",
            json={},
        )
        if not isinstance(data, dict):
            data = {"raw": data}

        session_id = _extract_ws_session_id(data)
        return WsSessionInfo(
            session_id=session_id,
            is_active=data.get("isActive"),
            is_connected=data.get("isConnected"),
            transfers_used=data.get("transfersUsed"),
            raw=data,
        )

    async def get_ws_session_status(self, session_id: str) -> WsSessionInfo:
        """
        Query WebSocket session status.

        ``GET /ws/sessions/{id}``
        """
        data = await self._request(
            "GET",
            f"/ws/sessions/{session_id}",
            label=f"/ws/sessions/{session_id}",
        )
        if not isinstance(data, dict):
            raise ArkhamApiError("WS session status returned unexpected format")
        return WsSessionInfo(
            session_id=session_id,
            is_active=data.get("isActive"),
            is_connected=data.get("isConnected"),
            transfers_used=data.get("transfersUsed"),
            raw=data,
        )


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _extract_ws_session_id(data: Dict[str, Any]) -> Optional[str]:
    for key in ("sessionId", "session_id", "id"):
        value = data.get(key)
        if value:
            return str(value).strip()
    nested = data.get("session")
    if isinstance(nested, dict):
        for key in ("sessionId", "session_id", "id"):
            value = nested.get(key)
            if value:
                return str(value).strip()
    return None


def _dedupe_addresses(addresses: List[str]) -> List[str]:
    return list(dict.fromkeys(
        addr.strip().lower()
        for addr in addresses
        if addr and addr.strip()
    ))


def _parse_batch_intel_response(data: Any) -> BatchAddressIntelligenceResponse:
    raw_addresses = data.get("addresses", {}) if isinstance(data, dict) else {}
    if not isinstance(raw_addresses, dict):
        return BatchAddressIntelligenceResponse()
    normalized = {
        str(addr).strip().lower(): value
        for addr, value in raw_addresses.items()
        if str(addr).strip()
    }
    return BatchAddressIntelligenceResponse(addresses=normalized)


def _parse_balances(data: Any) -> BalancesResponse:
    if isinstance(data, dict):
        obj = BalancesResponse.model_validate(data)
        obj.raw = data
        return obj
    if isinstance(data, list):
        return BalancesResponse(balances=data)
    return BalancesResponse()
