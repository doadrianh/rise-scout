from __future__ import annotations

from typing import Protocol

from rise_scout.domain.shared.types import AgentId


class RefreshFlagService(Protocol):
    def flag_agents(self, agent_ids: list[AgentId]) -> None: ...

    def pop_flagged_agents(self) -> list[AgentId]: ...
