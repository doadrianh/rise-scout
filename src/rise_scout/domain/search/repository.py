from __future__ import annotations

from typing import Protocol

from rise_scout.domain.search.models import ListingEvent, MatchedContact


class SearchRepository(Protocol):
    def find_matching_contacts(self, event: ListingEvent) -> list[MatchedContact]: ...
