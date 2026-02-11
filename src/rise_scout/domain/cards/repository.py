from __future__ import annotations

from typing import Protocol

from rise_scout.domain.cards.models import Card
from rise_scout.domain.shared.types import AgentId


class CardRepository(Protocol):
    def get(self, agent_id: AgentId) -> Card | None: ...

    def save(self, card: Card) -> None: ...
