from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from rise_scout.domain.shared.types import AgentId, ContactId


class CardContact(BaseModel):
    model_config = {"frozen": True}

    contact_id: ContactId
    name: str
    score: float
    top_reasons: list[str] = Field(default_factory=list)
    insight: str = ""


class Card(BaseModel):
    agent_id: AgentId
    contacts: list[CardContact] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ttl: int = 900  # 15 minutes in seconds
