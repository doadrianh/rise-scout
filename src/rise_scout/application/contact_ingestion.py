from __future__ import annotations

from typing import Any

import structlog

from rise_scout.application.event_handlers import dispatch_contact_events
from rise_scout.domain.contact.parsers import ContactChangeParser, InteractionParser
from rise_scout.domain.contact.repository import ContactRepository
from rise_scout.domain.embeddings.service import EmbeddingService
from rise_scout.domain.scoring.engine import ScoringEngine
from rise_scout.domain.shared.services import RefreshFlagService

logger = structlog.get_logger()


class ContactIngestionService:
    def __init__(
        self,
        contact_repo: ContactRepository,
        scoring_engine: ScoringEngine,
        embedding_service: EmbeddingService,
        refresh_flags: RefreshFlagService,
        contact_parser: ContactChangeParser,
        interaction_parser: InteractionParser,
    ) -> None:
        self._contact_repo = contact_repo
        self._scoring_engine = scoring_engine
        self._embedding_service = embedding_service
        self._refresh_flags = refresh_flags
        self._contact_parser = contact_parser
        self._interaction_parser = interaction_parser

    def handle_contact_change(self, payload: dict[str, Any]) -> None:
        contact, is_new = self._contact_parser.parse(payload)

        if not is_new:
            existing = self._contact_repo.get(contact.contact_id)
            if existing:
                contact.score = existing.score
                contact.score_reasons = existing.score_reasons

        self._scoring_engine.compute_profile_signals(contact)

        text = contact.to_embedding_text()
        if text.strip():
            contact.embedding_vector = self._embedding_service.embed(text)

        self._contact_repo.save(contact)
        dispatch_contact_events([contact], self._refresh_flags)

        logger.info(
            "contact_ingested",
            contact_id=str(contact.contact_id),
            is_new=is_new,
            score=contact.score,
        )

    def handle_interaction(self, payload: dict[str, Any]) -> None:
        contact_id, signal, detail = self._interaction_parser.parse(payload)

        contact = self._contact_repo.get(contact_id)
        if contact is None:
            logger.warning("interaction_contact_not_found", contact_id=str(contact_id))
            return

        self._scoring_engine.process_signal(contact, signal, detail)
        self._contact_repo.save(contact)
        dispatch_contact_events([contact], self._refresh_flags)

        logger.info(
            "interaction_processed",
            contact_id=str(contact_id),
            signal=signal.value,
            score=contact.score,
        )
