# arkham-intel-sdk

**[English](#english) | 中文**

非官方的 **Arkham Intelligence (Intel) API** Python SDK。

Arkham 官方 SDK 仅覆盖 *Exchange* API。本项目封装了 **Intel** 端点 —— 转账查询、地址情报、代币持仓、投资组合、Swap、余额、WebSocket 实时流等。

## 安装

```bash
# 本地开发安装
pip install -e /path/to/arkham-intel-sdk

# 发布后安装
pip install arkham-intel-sdk
```

## 快速开始

```python
import asyncio
from arkham_intel import AsyncArkhamIntelClient

async def main():
    async with AsyncArkhamIntelClient(api_key="your-api-key") as client:
        # 查询转账 — 返回类型化的 TransfersResponse
        resp = await client.get_transfers(chains="bsc", tokens="0x...", limit=50)
        for t in resp.transfers:
            print(t.id, t.historical_usd)

        # 地址情报 — 返回 AddressIntelligence
        intel = await client.get_address_intelligence("0xdead...")
        print(intel.arkham_entity)

        # 代币持仓快照
        holders = await client.get_token_holders_snapshot("bsc", "0x...")
        print(f"Top holders: {holders.total_holders}")

        # 搜索
        results = await client.search("binance")
        for r in results.results:
            print(r.name, r.type)

asyncio.run(main())
```

## WebSocket 实时流

```python
import asyncio
from arkham_intel import AsyncArkhamIntelClient, ArkhamIntelWebSocket

async def main():
    rest = AsyncArkhamIntelClient(api_key="your-api-key")
    ws = ArkhamIntelWebSocket(rest)

    async for transfer in ws.stream_transfers(chains=["bsc"], tokens=["0x..."]):
        print("New transfer:", transfer.get("id"))

asyncio.run(main())
```

## 已覆盖的端点

### 转账
| 方法 | 端点 | SDK 方法 |
|------|------|----------|
| GET | `/transfers` | `get_transfers()` |
| GET | `/transfers/tx/{hash}` | `get_transaction_transfers()` |
| GET | `/transfers/histogram` | `get_transfers_histogram()` |
| GET | `/tx/{hash}` | `get_transaction()` |

### 情报
| 方法 | 端点 | SDK 方法 |
|------|------|----------|
| GET | `/intelligence/address/{address}/all` | `get_address_intelligence()` |
| GET | `/intelligence/address/{address}` | `get_address_intelligence(chain=...)` |
| POST | `/intelligence/address/batch` | `get_address_intelligence_batch()` |
| POST | `/intelligence/address/batch/all` | `get_address_intelligence_batch_all()` |
| GET | `/intelligence/entity/{entity}` | `get_entity_intelligence()` |
| GET | `/intelligence/entity/{entity}/summary` | `get_entity_summary()` |
| GET | `/intelligence/entity_types` | `get_entity_types()` |
| GET | `/intelligence/contract/{chain}/{address}` | `get_contract_info()` |
| GET | `/intelligence/search` | `search()` |

### 代币
| 方法 | 端点 | SDK 方法 |
|------|------|----------|
| GET | `/token/holders/{chain}/{address}` | `get_token_holders_snapshot()` |
| GET | `/token/market/{id}` | `get_token_market()` |
| GET | `/token/price/history/{chain}/{address}` | `get_token_price_history()` |
| GET | `/token/top` | `get_token_top()` |
| GET | `/token/trending` | `get_token_trending()` |

### 余额 & 投资组合
| 方法 | 端点 | SDK 方法 |
|------|------|----------|
| GET | `/balances/address/{address}` | `get_address_balances()` |
| GET | `/balances/entity/{entity}` | `get_entity_balances()` |
| GET | `/portfolio/address/{address}` | `get_portfolio()` |
| GET | `/portfolio/entity/{entity}` | `get_entity_portfolio()` |
| GET | `/portfolio/timeSeries/address/{address}` | `get_portfolio_time_series()` |

### 分析
| 方法 | 端点 | SDK 方法 |
|------|------|----------|
| GET | `/counterparties/address/{address}` | `get_address_counterparties()` |
| GET | `/counterparties/entity/{entity}` | `get_entity_counterparties()` |
| GET | `/flow/address/{address}` | `get_address_flow()` |
| GET | `/flow/entity/{entity}` | `get_entity_flow()` |
| GET | `/history/address/{address}` | `get_address_history()` |
| GET | `/history/entity/{entity}` | `get_entity_history()` |
| GET | `/volume/address/{address}` | `get_address_volume()` |
| GET | `/volume/entity/{entity}` | `get_entity_volume()` |
| GET | `/swaps` | `get_swaps()` |

### 链 & WebSocket
| 方法 | 端点 | SDK 方法 |
|------|------|----------|
| GET | `/chains` | `get_chains()` |
| POST | `/ws/sessions` | `create_ws_session()` |
| GET | `/ws/sessions/{id}` | `get_ws_session_status()` |
| WS | `/ws/transfers` | `ArkhamIntelWebSocket.stream_transfers()` |

## 特性

- **异步优先** — 基于 `httpx`（REST）和 `aiohttp`（WebSocket）构建
- **共享 HTTP 客户端** — 通过 `async with` 上下文管理器复用连接
- **自动重试** — 429 / 5xx 时自动抖动退避重试，支持 `Retry-After` 响应头
- **Pydantic v2 模型** — snake_case 字段名 + camelCase 别名兼容 API；`extra="allow"` 保留未知字段
- **类型化响应** — 所有方法返回 Pydantic 模型，而非原始 dict
- **一致的错误处理** — 所有方法失败时抛出 `ArkhamApiError`
- **链名称标准化** — `eth` → `ethereum`、`bsc` → `bsc` 等，并支持 `GET /chains` 动态获取链列表
- **`py.typed` 标记** — 完整的类型检查器兼容性
- **零耦合** — 无数据库、无配置文件、无日志框架绑定

## 配置

```python
async with AsyncArkhamIntelClient(
    api_key="...",
    base_url="https://api.arkm.com",   # 默认值
    timeout=30.0,                        # 单次请求超时（秒）
    max_retries=10,                      # 429/5xx 重试次数
    max_retry_delay=5.0,                 # 重试间最大抖动延迟
    proxy="http://127.0.0.1:7890",       # 可选 HTTP 代理
) as client:
    ...
```

## 许可证

MIT

---

<a id="english"></a>

# arkham-intel-sdk

**English | [中文](#arkham-intel-sdk)**

Unofficial Python SDK for the **Arkham Intelligence (Intel) API**.

Arkham's official SDK only covers the *Exchange* API. This package wraps the **Intel** endpoints — transfers, address intelligence, token holders, portfolio, swaps, balances, WebSocket streams, and more.

## Installation

```bash
# From local path (development)
pip install -e /path/to/arkham-intel-sdk

# Or once published
pip install arkham-intel-sdk
```

## Quick Start

```python
import asyncio
from arkham_intel import AsyncArkhamIntelClient

async def main():
    async with AsyncArkhamIntelClient(api_key="your-api-key") as client:
        # Query transfers — returns typed TransfersResponse
        resp = await client.get_transfers(chains="bsc", tokens="0x...", limit=50)
        for t in resp.transfers:
            print(t.id, t.historical_usd)

        # Address intelligence — returns AddressIntelligence
        intel = await client.get_address_intelligence("0xdead...")
        print(intel.arkham_entity)

        # Token holders snapshot
        holders = await client.get_token_holders_snapshot("bsc", "0x...")
        print(f"Top holders: {holders.total_holders}")

        # Search
        results = await client.search("binance")
        for r in results.results:
            print(r.name, r.type)

asyncio.run(main())
```

## WebSocket Streaming

```python
import asyncio
from arkham_intel import AsyncArkhamIntelClient, ArkhamIntelWebSocket

async def main():
    rest = AsyncArkhamIntelClient(api_key="your-api-key")
    ws = ArkhamIntelWebSocket(rest)

    async for transfer in ws.stream_transfers(chains=["bsc"], tokens=["0x..."]):
        print("New transfer:", transfer.get("id"))

asyncio.run(main())
```

## Covered Endpoints

### Transfers
| Method | Endpoint | SDK Method |
|--------|----------|------------|
| GET | `/transfers` | `get_transfers()` |
| GET | `/transfers/tx/{hash}` | `get_transaction_transfers()` |
| GET | `/transfers/histogram` | `get_transfers_histogram()` |
| GET | `/tx/{hash}` | `get_transaction()` |

### Intelligence
| Method | Endpoint | SDK Method |
|--------|----------|------------|
| GET | `/intelligence/address/{address}/all` | `get_address_intelligence()` |
| GET | `/intelligence/address/{address}` | `get_address_intelligence(chain=...)` |
| POST | `/intelligence/address/batch` | `get_address_intelligence_batch()` |
| POST | `/intelligence/address/batch/all` | `get_address_intelligence_batch_all()` |
| GET | `/intelligence/entity/{entity}` | `get_entity_intelligence()` |
| GET | `/intelligence/entity/{entity}/summary` | `get_entity_summary()` |
| GET | `/intelligence/entity_types` | `get_entity_types()` |
| GET | `/intelligence/contract/{chain}/{address}` | `get_contract_info()` |
| GET | `/intelligence/search` | `search()` |

### Token
| Method | Endpoint | SDK Method |
|--------|----------|------------|
| GET | `/token/holders/{chain}/{address}` | `get_token_holders_snapshot()` |
| GET | `/token/market/{id}` | `get_token_market()` |
| GET | `/token/price/history/{chain}/{address}` | `get_token_price_history()` |
| GET | `/token/top` | `get_token_top()` |
| GET | `/token/trending` | `get_token_trending()` |

### Balances & Portfolio
| Method | Endpoint | SDK Method |
|--------|----------|------------|
| GET | `/balances/address/{address}` | `get_address_balances()` |
| GET | `/balances/entity/{entity}` | `get_entity_balances()` |
| GET | `/portfolio/address/{address}` | `get_portfolio()` |
| GET | `/portfolio/entity/{entity}` | `get_entity_portfolio()` |
| GET | `/portfolio/timeSeries/address/{address}` | `get_portfolio_time_series()` |

### Analytics
| Method | Endpoint | SDK Method |
|--------|----------|------------|
| GET | `/counterparties/address/{address}` | `get_address_counterparties()` |
| GET | `/counterparties/entity/{entity}` | `get_entity_counterparties()` |
| GET | `/flow/address/{address}` | `get_address_flow()` |
| GET | `/flow/entity/{entity}` | `get_entity_flow()` |
| GET | `/history/address/{address}` | `get_address_history()` |
| GET | `/history/entity/{entity}` | `get_entity_history()` |
| GET | `/volume/address/{address}` | `get_address_volume()` |
| GET | `/volume/entity/{entity}` | `get_entity_volume()` |
| GET | `/swaps` | `get_swaps()` |

### Chains & WebSocket
| Method | Endpoint | SDK Method |
|--------|----------|------------|
| GET | `/chains` | `get_chains()` |
| POST | `/ws/sessions` | `create_ws_session()` |
| GET | `/ws/sessions/{id}` | `get_ws_session_status()` |
| WS | `/ws/transfers` | `ArkhamIntelWebSocket.stream_transfers()` |

## Features

- **Async-first** — built on `httpx` (REST) and `aiohttp` (WebSocket)
- **Shared HTTP client** — `async with` context manager for connection reuse
- **Automatic retry** with jitter backoff on 429 / 5xx, respects `Retry-After` header
- **Pydantic v2 models** — snake_case fields with camelCase aliases for API compatibility; `extra="allow"` preserves unknown fields
- **Typed responses** — all methods return Pydantic models, not raw dicts
- **Consistent error handling** — all methods raise `ArkhamApiError` on failure
- **Chain name normalization** (`eth` → `ethereum`, `bsc` → `bsc`, etc.) + `GET /chains` for dynamic chain list
- **`py.typed` marker** — full type-checker compatibility
- **Zero project coupling** — no database, no config files, no logging framework lock-in

## Configuration

```python
async with AsyncArkhamIntelClient(
    api_key="...",
    base_url="https://api.arkm.com",   # default
    timeout=30.0,                        # per-request timeout (seconds)
    max_retries=10,                      # retry count for 429/5xx
    max_retry_delay=5.0,                 # max jitter delay between retries
    proxy="http://127.0.0.1:7890",       # optional HTTP proxy
) as client:
    ...
```

## License

MIT
