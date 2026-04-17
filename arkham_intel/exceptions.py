class ArkhamApiError(RuntimeError):
    """Raised when the Arkham API returns an error after all retries are exhausted."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 0,
        attempts: int = 1,
        rate_limit_hits: int = 0,
        retry_sleep_seconds: float = 0.0,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.attempts = attempts
        self.rate_limit_hits = rate_limit_hits
        self.retry_sleep_seconds = retry_sleep_seconds


class ArkhamRateLimitError(ArkhamApiError):
    """Raised specifically when rate-limited (HTTP 429) and retries are exhausted."""

    pass


class ArkhamWebSocketError(ArkhamApiError):
    """Raised on WebSocket-level failures."""

    pass
