from __future__ import annotations

from typing import Any, Protocol

from rise_scout.domain.search.models import ListingEvent


class ListingParser(Protocol):
    def parse(self, payload: dict[str, Any]) -> ListingEvent: ...
