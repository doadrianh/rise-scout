from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from rise_scout.domain.shared.types import AgentId, ContactId


class DomainEvent(BaseModel):
    model_config = {"frozen": True}

    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ContactScored(DomainEvent):
    contact_id: ContactId
    agent_ids: list[AgentId]
