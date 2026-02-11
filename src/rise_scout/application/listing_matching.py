from __future__ import annotations

from typing import Any

import structlog

from rise_scout.application.event_handlers import dispatch_contact_events
from rise_scout.domain.contact.repository import ContactRepository
from rise_scout.domain.scoring.engine import ScoringEngine
from rise_scout.domain.scoring.signals import LISTING_EVENT_SIGNAL_MAP
from rise_scout.domain.search.parsers import ListingParser
from rise_scout.domain.search.repository import SearchRepository
from rise_scout.domain.shared.services import RefreshFlagService

logger = structlog.get_logger()


class ListingMatchingService:
    def __init__(
        self,
        contact_repo: ContactRepository,
        search_repo: SearchRepository,
        scoring_engine: ScoringEngine,
        refresh_flags: RefreshFlagService,
        listing_parser: ListingParser,
    ) -> None:
        self._contact_repo = contact_repo
        self._search_repo = search_repo
        self._scoring_engine = scoring_engine
        self._refresh_flags = refresh_flags
        self._listing_parser = listing_parser

    def handle_listing_event(self, payload: dict[str, Any]) -> None:
        event = self._listing_parser.parse(payload)
        matched = self._search_repo.find_matching_contacts(event)

        if not matched:
            logger.info("no_matches", listing_id=str(event.listing_id))
            return

        contact_ids = [m.contact_id for m in matched]
        contacts = self._contact_repo.bulk_get(contact_ids)
        contacts_by_id = {c.contact_id: c for c in contacts}

        signal = LISTING_EVENT_SIGNAL_MAP.get(event.event_type)
        if signal is None:
            logger.warning("unmapped_event_type", event_type=event.event_type)
            return

        for match in matched:
            contact = contacts_by_id.get(match.contact_id)
            if contact is None:
                continue
            detail = "; ".join(match.match_reasons)
            self._scoring_engine.process_signal(contact, signal, detail)

        modified = [contacts_by_id[m.contact_id] for m in matched if m.contact_id in contacts_by_id]
        self._contact_repo.bulk_save(modified)
        dispatch_contact_events(modified, self._refresh_flags)

        logger.info(
            "listing_matching_complete",
            listing_id=str(event.listing_id),
            matched=len(matched),
            scored=len(modified),
        )
