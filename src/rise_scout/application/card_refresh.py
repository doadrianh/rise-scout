from __future__ import annotations

import structlog

from rise_scout.domain.cards.llm_service import LLMEnrichmentService
from rise_scout.domain.cards.models import Card, CardContact
from rise_scout.domain.cards.repository import CardRepository
from rise_scout.domain.contact.models import Contact
from rise_scout.domain.contact.repository import ContactRepository
from rise_scout.domain.shared.services import RefreshFlagService

logger = structlog.get_logger()


class CardRefreshService:
    def __init__(
        self,
        contact_repo: ContactRepository,
        card_repo: CardRepository,
        llm_service: LLMEnrichmentService,
        refresh_flags: RefreshFlagService,
    ) -> None:
        self._contact_repo = contact_repo
        self._card_repo = card_repo
        self._llm_service = llm_service
        self._refresh_flags = refresh_flags

    def refresh_flagged_agents(self) -> int:
        agent_ids = self._refresh_flags.pop_flagged_agents()
        if not agent_ids:
            logger.info("no_agents_flagged")
            return 0

        top_contacts = self._contact_repo.get_top_by_agents(agent_ids, limit=5)
        refreshed = 0

        for agent_id in agent_ids:
            contacts = top_contacts.get(agent_id, [])
            if not contacts:
                continue

            card_contacts = [self._build_card_contact(c) for c in contacts]
            card = Card(agent_id=agent_id, contacts=card_contacts)
            self._card_repo.save(card)
            refreshed += 1

        logger.info("card_refresh_complete", agents=len(agent_ids), refreshed=refreshed)
        return refreshed

    def _build_card_contact(self, contact: Contact) -> CardContact:
        return CardContact(
            contact_id=contact.contact_id,
            name=contact.display_name,
            score=contact.score,
            top_reasons=contact.top_score_details(limit=3),
            insight=self._generate_insight_safe(contact),
        )

    def _generate_insight_safe(self, contact: Contact) -> str:
        try:
            return self._llm_service.generate_insight(contact)
        except Exception:
            logger.warning(
                "insight_generation_failed",
                contact_id=str(contact.contact_id),
                exc_info=True,
            )
            return ""
