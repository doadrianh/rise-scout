from __future__ import annotations

from typing import Any, Protocol

import structlog

from rise_scout.domain.shared.types import AgentId, ContactId

logger = structlog.get_logger()


class RiseApiClient(Protocol):
    def get_contact_listing_count(self, contact_id: ContactId) -> int: ...

    def get_agent_contacts(self, agent_id: AgentId) -> list[dict[str, Any]]: ...


class StubRiseApiClient:
    """Stub implementation returning mock data. Real implementation later."""

    def get_contact_listing_count(self, contact_id: ContactId) -> int:
        logger.debug(
            "stub_rise_api", method="get_contact_listing_count", contact_id=str(contact_id)
        )
        return 3

    def get_agent_contacts(self, agent_id: AgentId) -> list[dict[str, Any]]:
        logger.debug("stub_rise_api", method="get_agent_contacts", agent_id=str(agent_id))
        return []
