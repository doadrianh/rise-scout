from __future__ import annotations

from enum import StrEnum

from rise_scout.domain.search.models import ListingEventType


class SignalType(StrEnum):
    # Profile signals
    PREFERENCES_COMPLETE = "preferences_complete"
    HAS_EMAIL = "has_email"
    HAS_PHONE = "has_phone"
    MULTI_AGENT = "multi_agent"

    # Engagement signals
    LISTING_VIEW = "listing_view"
    LISTING_SAVE = "listing_save"
    LISTING_SHARE = "listing_share"
    SEARCH_PERFORMED = "search_performed"
    OPEN_HOUSE_RSVP = "open_house_rsvp"
    DOCUMENT_SIGNED = "document_signed"

    # Market signals
    PRICE_DROP_MATCH = "price_drop_match"
    NEW_LISTING_MATCH = "new_listing_match"
    STATUS_CHANGE_MATCH = "status_change_match"
    BACK_ON_MARKET_MATCH = "back_on_market_match"

    # Relationship signals
    AGENT_NOTE_ADDED = "agent_note_added"
    CONTACTED_RECENTLY = "contacted_recently"

    @property
    def category(self) -> str:
        categories: dict[str, list[SignalType]] = {
            "profile": [
                SignalType.PREFERENCES_COMPLETE,
                SignalType.HAS_EMAIL,
                SignalType.HAS_PHONE,
                SignalType.MULTI_AGENT,
            ],
            "engagement": [
                SignalType.LISTING_VIEW,
                SignalType.LISTING_SAVE,
                SignalType.LISTING_SHARE,
                SignalType.SEARCH_PERFORMED,
                SignalType.OPEN_HOUSE_RSVP,
                SignalType.DOCUMENT_SIGNED,
            ],
            "market": [
                SignalType.PRICE_DROP_MATCH,
                SignalType.NEW_LISTING_MATCH,
                SignalType.STATUS_CHANGE_MATCH,
                SignalType.BACK_ON_MARKET_MATCH,
            ],
            "relationship": [
                SignalType.AGENT_NOTE_ADDED,
                SignalType.CONTACTED_RECENTLY,
            ],
        }
        for cat, signals in categories.items():
            if self in signals:
                return cat
        return "unknown"


LISTING_EVENT_SIGNAL_MAP: dict[ListingEventType, SignalType] = {
    ListingEventType.NEW_LISTING: SignalType.NEW_LISTING_MATCH,
    ListingEventType.PRICE_CHANGE: SignalType.PRICE_DROP_MATCH,
    ListingEventType.STATUS_CHANGE: SignalType.STATUS_CHANGE_MATCH,
    ListingEventType.BACK_ON_MARKET: SignalType.BACK_ON_MARKET_MATCH,
}
