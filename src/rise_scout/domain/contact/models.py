from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, PrivateAttr

from rise_scout.domain.shared.events import ContactScored, DomainEvent
from rise_scout.domain.shared.types import AgentId, ContactId, ListingId, MlsId

MAX_REASONS = 50


class PropertyType(StrEnum):
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    LAND = "land"
    OTHER = "other"


class Preferences(BaseModel):
    price_min: float | None = None
    price_max: float | None = None
    beds_min: int | None = None
    beds_max: int | None = None
    baths_min: int | None = None
    baths_max: int | None = None
    sqft_min: int | None = None
    sqft_max: int | None = None
    property_types: list[PropertyType] = Field(default_factory=list)
    zip_codes: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return bool(
            self.price_min is not None
            and self.price_max is not None
            and (self.zip_codes or self.cities)
        )


class ScoreReason(BaseModel):
    model_config = {"frozen": True}

    signal: str
    points: float
    category: str
    detail: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Contact(BaseModel):
    contact_id: ContactId
    user_ids: list[AgentId] = Field(default_factory=list)
    organisationalunit_id: str | None = None
    mls_ids: list[MlsId] = Field(default_factory=list)

    first_name: str = ""
    last_name: str = ""
    email: str | None = None
    phone: str | None = None

    preferences: Preferences = Field(default_factory=Preferences)
    watched_listings: list[ListingId] = Field(default_factory=list)

    score: float = 0.0
    score_reasons: list[ScoreReason] = Field(default_factory=list)
    embedding_vector: list[float] | None = None

    last_interaction_at: datetime | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    _pending_events: list[DomainEvent] = PrivateAttr(default_factory=list)

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def to_embedding_text(self) -> str:
        parts = [
            self.first_name,
            self.last_name,
            " ".join(self.preferences.keywords),
            " ".join(self.preferences.cities),
            " ".join(self.preferences.zip_codes),
        ]
        return " ".join(part for part in parts if part)

    def top_score_details(self, limit: int = 3) -> list[str]:
        return [r.detail for r in self.score_reasons[:limit]]

    def apply_score_delta(self, delta: float, reason: ScoreReason) -> None:
        self.score = max(0.0, self.score + delta)
        self.score_reasons.insert(0, reason)
        self.trim_reasons()
        self.updated_at = datetime.now(UTC)
        self._pending_events.append(
            ContactScored(
                contact_id=self.contact_id,
                agent_ids=list(self.user_ids),
            )
        )

    def apply_decay(self, factor: float) -> None:
        self.score = max(0.0, self.score * factor)
        self.updated_at = datetime.now(UTC)

    def trim_reasons(self, max_reasons: int = MAX_REASONS) -> None:
        if len(self.score_reasons) > max_reasons:
            self.score_reasons = self.score_reasons[:max_reasons]

    def collect_events(self) -> list[DomainEvent]:
        events = list(self._pending_events)
        self._pending_events.clear()
        return events
