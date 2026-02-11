from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from rise_scout.domain.shared.types import ContactId, ListingId, MlsId


class ListingEventType(StrEnum):
    NEW_LISTING = "new_listing"
    PRICE_CHANGE = "price_change"
    STATUS_CHANGE = "status_change"
    BACK_ON_MARKET = "back_on_market"


class ListingEvent(BaseModel):
    model_config = {"frozen": True}

    listing_id: ListingId
    event_type: ListingEventType
    mls_id: MlsId

    price: float | None = None
    previous_price: float | None = None
    status: str | None = None
    beds: int | None = None
    baths: int | None = None
    sqft: int | None = None
    property_type: str | None = None
    zip_code: str | None = None
    city: str | None = None
    lat: float | None = None
    lon: float | None = None


class MatchedContact(BaseModel):
    model_config = {"frozen": True}

    contact_id: ContactId
    match_reasons: list[str] = Field(default_factory=list)
