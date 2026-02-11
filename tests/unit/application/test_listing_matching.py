from __future__ import annotations

from typing import Any

from rise_scout.application.listing_matching import ListingMatchingService
from rise_scout.domain.contact.models import Contact
from rise_scout.domain.scoring.engine import ScoringEngine
from rise_scout.domain.scoring.weights import ScoringWeights
from rise_scout.domain.search.models import ListingEvent, ListingEventType, MatchedContact
from rise_scout.domain.shared.types import AgentId, ContactId, ListingId, MlsId


class FakeContactRepo:
    def __init__(self):
        self.contacts: dict[str, Contact] = {}

    def get(self, contact_id):
        return self.contacts.get(str(contact_id))

    def save(self, contact):
        self.contacts[str(contact.contact_id)] = contact

    def bulk_get(self, contact_ids):
        return [self.contacts[str(cid)] for cid in contact_ids if str(cid) in self.contacts]

    def bulk_save(self, contacts):
        for c in contacts:
            self.save(c)

    def get_top_by_agents(self, agent_ids, limit=5):
        return {}

    def paginate_all(self, page_size=500):
        return list(self.contacts.values())


class FakeSearchRepo:
    def __init__(self, matches: list[MatchedContact] | None = None):
        self.matches = matches or []

    def find_matching_contacts(self, event):
        return self.matches


class FakeRefreshFlags:
    def __init__(self):
        self.flagged: list[AgentId] = []

    def flag_agents(self, agent_ids):
        self.flagged.extend(agent_ids)

    def pop_flagged_agents(self):
        result = list(self.flagged)
        self.flagged.clear()
        return result


class FakeListingParser:
    def parse(self, payload: dict[str, Any]) -> ListingEvent:
        return ListingEvent(
            listing_id=ListingId(str(payload["listing_id"])),
            event_type=ListingEventType(payload["event_type"]),
            mls_id=MlsId(str(payload["mls_id"])),
            price=payload.get("price"),
            zip_code=payload.get("zip_code"),
        )


class TestListingMatchingService:
    def test_scores_matching_contacts(self, scoring_weights: ScoringWeights):
        contact = Contact(
            contact_id=ContactId("c-1"),
            user_ids=[AgentId("a-1")],
            mls_ids=[MlsId("mls-1")],
        )
        repo = FakeContactRepo()
        repo.save(contact)

        matches = [MatchedContact(contact_id=ContactId("c-1"), match_reasons=["price match"])]
        search = FakeSearchRepo(matches)
        flags = FakeRefreshFlags()

        service = ListingMatchingService(
            contact_repo=repo,
            search_repo=search,
            scoring_engine=ScoringEngine(scoring_weights),
            refresh_flags=flags,
            listing_parser=FakeListingParser(),
        )

        service.handle_listing_event(
            {
                "listing_id": "l-1",
                "event_type": "new_listing",
                "mls_id": "mls-1",
                "price": 400000,
            }
        )

        saved = repo.contacts["c-1"]
        assert saved.score == 10.0  # new_listing_match = 10
        assert AgentId("a-1") in flags.flagged

    def test_no_matches_does_nothing(self, scoring_weights: ScoringWeights):
        repo = FakeContactRepo()
        search = FakeSearchRepo([])
        flags = FakeRefreshFlags()

        service = ListingMatchingService(
            contact_repo=repo,
            search_repo=search,
            scoring_engine=ScoringEngine(scoring_weights),
            refresh_flags=flags,
            listing_parser=FakeListingParser(),
        )

        service.handle_listing_event(
            {
                "listing_id": "l-1",
                "event_type": "new_listing",
                "mls_id": "mls-1",
            }
        )

        assert len(flags.flagged) == 0
