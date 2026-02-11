from __future__ import annotations

from typing import Any

import structlog
from opensearchpy import OpenSearch

from rise_scout.domain.search.models import ListingEvent, MatchedContact
from rise_scout.domain.shared.types import ContactId

logger = structlog.get_logger()


class OpenSearchSearchRepository:
    def __init__(self, client: OpenSearch, contacts_index: str) -> None:
        self._client = client
        self._contacts_index = contacts_index

    def find_matching_contacts(self, event: ListingEvent) -> list[MatchedContact]:
        query = self._build_inverted_query(event)
        body: dict[str, Any] = {
            "query": query,
            "size": 200,
            "_source": ["contact_id"],
        }

        resp = self._client.search(index=self._contacts_index, body=body)
        hits = resp["hits"]["hits"]

        matched = []
        for hit in hits:
            reasons = self._extract_match_reasons(hit, event)
            matched.append(
                MatchedContact(
                    contact_id=ContactId(hit["_source"]["contact_id"]),
                    match_reasons=reasons,
                )
            )

        logger.info(
            "inverted_search_complete",
            listing_id=str(event.listing_id),
            matches=len(matched),
        )
        return matched

    def _build_inverted_query(self, event: ListingEvent) -> dict[str, Any]:
        must: list[dict[str, Any]] = [{"term": {"mls_ids": str(event.mls_id)}}]

        should: list[dict[str, Any]] = []
        minimum_should_match = 1

        if event.price is not None:
            should.append(
                {
                    "bool": {
                        "must": [
                            {"range": {"preferences.price_min": {"lte": event.price}}},
                            {"range": {"preferences.price_max": {"gte": event.price}}},
                        ]
                    }
                }
            )

        if event.beds is not None:
            should.append(
                {
                    "bool": {
                        "must": [
                            {"range": {"preferences.beds_min": {"lte": event.beds}}},
                            {"range": {"preferences.beds_max": {"gte": event.beds}}},
                        ]
                    }
                }
            )

        if event.zip_code:
            should.append({"term": {"preferences.zip_codes": event.zip_code}})

        if event.city:
            should.append({"term": {"preferences.cities": event.city.lower()}})

        if event.property_type:
            should.append({"term": {"preferences.property_types": event.property_type}})

        # Also match contacts watching this listing
        should.append({"term": {"watched_listings": str(event.listing_id)}})

        if not should:
            minimum_should_match = 0

        return {
            "bool": {
                "must": must,
                "should": should,
                "minimum_should_match": minimum_should_match,
            }
        }

    def _extract_match_reasons(self, hit: dict[str, Any], event: ListingEvent) -> list[str]:
        reasons = []
        reasons.append(f"{event.event_type.value} for listing {event.listing_id}")
        if event.price is not None:
            reasons.append(f"Price ${event.price:,.0f}")
        if event.zip_code:
            reasons.append(f"Location: {event.zip_code}")
        return reasons
