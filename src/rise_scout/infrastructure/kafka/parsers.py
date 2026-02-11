from __future__ import annotations

from typing import Any

import structlog

from rise_scout.domain.contact.models import Contact, Preferences
from rise_scout.domain.scoring.signals import SignalType
from rise_scout.domain.search.models import ListingEvent, ListingEventType
from rise_scout.domain.shared.types import AgentId, ContactId, ListingId, MlsId

logger = structlog.get_logger()


class ContactChangeParser:
    def parse(self, payload: dict[str, Any]) -> tuple[Contact, bool]:
        contact_id = ContactId(str(payload["contact_id"]))
        is_new = payload.get("event_type") == "create"

        prefs_data = payload.get("preferences", {})
        preferences = Preferences(
            price_min=prefs_data.get("price_min"),
            price_max=prefs_data.get("price_max"),
            beds_min=prefs_data.get("beds_min"),
            beds_max=prefs_data.get("beds_max"),
            baths_min=prefs_data.get("baths_min"),
            baths_max=prefs_data.get("baths_max"),
            sqft_min=prefs_data.get("sqft_min"),
            sqft_max=prefs_data.get("sqft_max"),
            property_types=prefs_data.get("property_types", []),
            zip_codes=prefs_data.get("zip_codes", []),
            cities=prefs_data.get("cities", []),
            keywords=prefs_data.get("keywords", []),
        )

        contact = Contact(
            contact_id=contact_id,
            user_ids=[AgentId(str(uid)) for uid in payload.get("user_ids", [])],
            organisationalunit_id=payload.get("organisationalunit_id"),
            mls_ids=[MlsId(str(mid)) for mid in payload.get("mls_ids", [])],
            first_name=payload.get("first_name", ""),
            last_name=payload.get("last_name", ""),
            email=payload.get("email"),
            phone=payload.get("phone"),
            preferences=preferences,
            watched_listings=[ListingId(str(lid)) for lid in payload.get("watched_listings", [])],
        )

        logger.info(
            "contact_parsed",
            contact_id=str(contact_id),
            is_new=is_new,
        )
        return contact, is_new


class InteractionParser:
    SIGNAL_MAP: dict[str, SignalType] = {
        "listing_view": SignalType.LISTING_VIEW,
        "listing_save": SignalType.LISTING_SAVE,
        "listing_share": SignalType.LISTING_SHARE,
        "search_performed": SignalType.SEARCH_PERFORMED,
        "open_house_rsvp": SignalType.OPEN_HOUSE_RSVP,
        "document_signed": SignalType.DOCUMENT_SIGNED,
        "agent_note_added": SignalType.AGENT_NOTE_ADDED,
        "contacted_recently": SignalType.CONTACTED_RECENTLY,
    }

    def parse(self, payload: dict[str, Any]) -> tuple[ContactId, SignalType, str]:
        contact_id = ContactId(str(payload["contact_id"]))
        raw_type = payload["interaction_type"]
        signal = self.SIGNAL_MAP.get(raw_type)

        if signal is None:
            raise ValueError(f"Unknown interaction type: {raw_type}")

        detail = payload.get("detail", "")
        logger.info(
            "interaction_parsed",
            contact_id=str(contact_id),
            signal=signal.value,
        )
        return contact_id, signal, detail


class ListingParser:
    EVENT_TYPE_MAP: dict[str, ListingEventType] = {
        "new": ListingEventType.NEW_LISTING,
        "price_change": ListingEventType.PRICE_CHANGE,
        "status_change": ListingEventType.STATUS_CHANGE,
        "back_on_market": ListingEventType.BACK_ON_MARKET,
    }

    def parse(self, payload: dict[str, Any]) -> ListingEvent:
        raw_event_type = payload.get("event_type", "new")
        event_type = self.EVENT_TYPE_MAP.get(raw_event_type)
        if event_type is None:
            raise ValueError(f"Unknown listing event type: {raw_event_type}")

        event = ListingEvent(
            listing_id=ListingId(str(payload["listing_id"])),
            event_type=event_type,
            mls_id=MlsId(str(payload["mls_id"])),
            price=payload.get("price"),
            previous_price=payload.get("previous_price"),
            status=payload.get("status"),
            beds=payload.get("beds"),
            baths=payload.get("baths"),
            sqft=payload.get("sqft"),
            property_type=payload.get("property_type"),
            zip_code=payload.get("zip_code"),
            city=payload.get("city"),
            lat=payload.get("lat"),
            lon=payload.get("lon"),
        )
        logger.info(
            "listing_parsed",
            listing_id=str(event.listing_id),
            event_type=event_type.value,
        )
        return event
