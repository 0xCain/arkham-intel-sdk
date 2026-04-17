import asyncio
import logging
import random
from typing import Any, Dict, Optional, Tuple

import httpx

from .exceptions import ArkhamApiError, ArkhamRateLimitError
from ._constants import DEFAULT_MAX_RETRIES, DEFAULT_MAX_RETRY_DELAY, DEFAULT_MIN_RETRY_DELAY

logger = logging.getLogger("arkham_intel")


def _should_retry(status_code: int) -> bool:
    return status_code == 429 or status_code >= 500


def _jitter_delay(min_delay: float, max_delay: float) -> float:
    return random.uniform(min_delay, max_delay)


def _parse_retry_after(response: httpx.Response) -> Optional[float]:
    """Extract ``Retry-After`` header value as seconds, or *None*."""
    raw = response.headers.get("Retry-After") or response.headers.get("retry-after")
    if not raw:
        return None
    raw = raw.strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        pass
    # RFC 7231 HTTP-date format is rare for APIs; ignore it here.
    return None


async def request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    label: str = "",
    max_retries: int = DEFAULT_MAX_RETRIES,
    max_delay: float = DEFAULT_MAX_RETRY_DELAY,
    min_delay: float = DEFAULT_MIN_RETRY_DELAY,
    **kwargs: Any,
) -> Tuple[Any, Dict[str, Any]]:
    """
    Execute an HTTP request with automatic retry on 429 / 5xx.

    When a ``Retry-After`` header is present on a 429 response, the delay
    is taken from the header (clamped to *max_delay*) instead of using
    random jitter.

    Returns ``(parsed_json, meta)`` where *meta* contains retry statistics.
    """
    attempts = 0
    rate_limit_hits = 0
    total_sleep = 0.0

    while True:
        attempts += 1
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json(), {
                "attempts": attempts,
                "rate_limited": rate_limit_hits > 0,
                "rate_limit_hits": rate_limit_hits,
                "retry_sleep_seconds": total_sleep,
            }
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            body = (exc.response.text or "").strip()[:500]

            if status_code == 429:
                rate_limit_hits += 1

            if attempts <= max_retries and _should_retry(status_code):
                retry_after = _parse_retry_after(exc.response)
                if retry_after is not None:
                    delay = min(retry_after, max_delay)
                else:
                    delay = _jitter_delay(min_delay, max_delay)
                total_sleep += delay
                logger.warning(
                    "%s failed (status=%d), retrying in %.2fs (%d/%d)%s",
                    label, status_code, delay, attempts, max_retries,
                    " [Retry-After]" if retry_after is not None else "",
                )
                await asyncio.sleep(delay)
                continue

            error_cls = ArkhamRateLimitError if status_code == 429 else ArkhamApiError
            raise error_cls(
                f"{label} request failed: HTTP {status_code}"
                + (f" body={body}" if body else ""),
                status_code=status_code,
                attempts=attempts,
                rate_limit_hits=rate_limit_hits,
                retry_sleep_seconds=total_sleep,
            ) from exc

        except (httpx.RequestError, ValueError) as exc:
            if attempts <= max_retries:
                delay = _jitter_delay(min_delay, max_delay)
                total_sleep += delay
                logger.warning(
                    "%s error (%s), retrying in %.2fs (%d/%d)",
                    label, type(exc).__name__, delay, attempts, max_retries,
                )
                await asyncio.sleep(delay)
                continue

            raise ArkhamApiError(
                f"{label} request failed: {exc}",
                attempts=attempts,
                rate_limit_hits=rate_limit_hits,
                retry_sleep_seconds=total_sleep,
            ) from exc
