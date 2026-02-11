from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from rise_scout.domain.shared.types import AgentId

if TYPE_CHECKING:
    import redis

logger = structlog.get_logger()

REFRESH_KEY = "rise_scout:refresh_flags"


class RefreshFlagStore:
    def __init__(self, client: redis.Redis[bytes]) -> None:
        self._client = client

    def flag_agents(self, agent_ids: list[AgentId]) -> None:
        if not agent_ids:
            return
        self._client.sadd(REFRESH_KEY, *[str(aid) for aid in agent_ids])
        logger.debug("agents_flagged", count=len(agent_ids))

    def pop_flagged_agents(self) -> list[AgentId]:
        members: set[bytes] = self._client.smembers(REFRESH_KEY)
        if not members:
            return []
        self._client.delete(REFRESH_KEY)
        agent_ids = [AgentId(m.decode()) for m in members]
        logger.info("flagged_agents_popped", count=len(agent_ids))
        return agent_ids
