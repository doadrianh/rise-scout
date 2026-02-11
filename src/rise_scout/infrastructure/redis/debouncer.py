from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    import redis

logger = structlog.get_logger()


class EventDebouncer:
    def __init__(self, client: redis.Redis[bytes], prefix: str = "rise_scout:debounce") -> None:
        self._client = client
        self._prefix = prefix

    def should_process(self, key: str, ttl_seconds: int = 60) -> bool:
        full_key = f"{self._prefix}:{key}"
        result = self._client.set(full_key, "1", nx=True, ex=ttl_seconds)
        if result:
            logger.debug("debounce_pass", key=key)
            return True
        logger.debug("debounce_skip", key=key)
        return False
