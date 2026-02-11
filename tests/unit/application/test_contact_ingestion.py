from __future__ import annotations

from typing import Any

from rise_scout.application.contact_ingestion import ContactIngestionService
from rise_scout.domain.contact.models import Contact, Preferences
from rise_scout.domain.scoring.engine import ScoringEngine
from rise_scout.domain.scoring.signals import SignalType
from rise_scout.domain.scoring.weights import ScoringWeights
from rise_scout.domain.shared.types import AgentId, ContactId


class FakeContactRepo:
    def __init__(self):
        self.contacts: dict[str, Contact] = {}

    def get(self, contact_id: ContactId) -> Contact | None:
        return self.contacts.get(str(contact_id))

    def save(self, contact: Contact) -> None:
        self.contacts[str(contact.contact_id)] = contact

    def bulk_get(self, contact_ids: list[ContactId]) -> list[Contact]:
        return [self.contacts[str(cid)] for cid in contact_ids if str(cid) in self.contacts]

    def bulk_save(self, contacts: list[Contact]) -> None:
        for c in contacts:
            self.save(c)

    def get_top_by_agents(self, agent_ids, limit=5):
        return {}

    def paginate_all(self, page_size=500):
        return list(self.contacts.values())


class FakeEmbeddingService:
    def embed(self, text: str) -> list[float]:
        return [0.1] * 10

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class FakeRefreshFlags:
    def __init__(self):
        self.flagged: list[AgentId] = []

    def flag_agents(self, agent_ids: list[AgentId]) -> None:
        self.flagged.extend(agent_ids)

    def pop_flagged_agents(self) -> list[AgentId]:
        result = list(self.flagged)
        self.flagged.clear()
        return result


class FakeContactParser:
    def parse(self, payload: dict[str, Any]) -> tuple[Contact, bool]:
        return Contact(
            contact_id=ContactId(str(payload["contact_id"])),
            user_ids=[AgentId(str(uid)) for uid in payload.get("user_ids", [])],
            first_name=payload.get("first_name", ""),
            last_name=payload.get("last_name", ""),
            email=payload.get("email"),
            preferences=Preferences(
                price_min=payload.get("price_min"),
                price_max=payload.get("price_max"),
                zip_codes=payload.get("zip_codes", []),
            ),
        ), payload.get("event_type") == "create"


class FakeInteractionParser:
    def parse(self, payload: dict[str, Any]) -> tuple[ContactId, SignalType, str]:
        return (
            ContactId(str(payload["contact_id"])),
            SignalType(payload["interaction_type"]),
            payload.get("detail", ""),
        )


class TestContactIngestionService:
    def _build_service(self, scoring_weights: ScoringWeights):
        self.repo = FakeContactRepo()
        self.embedding = FakeEmbeddingService()
        self.flags = FakeRefreshFlags()
        return ContactIngestionService(
            contact_repo=self.repo,
            scoring_engine=ScoringEngine(scoring_weights),
            embedding_service=self.embedding,
            refresh_flags=self.flags,
            contact_parser=FakeContactParser(),
            interaction_parser=FakeInteractionParser(),
        )

    def test_handle_new_contact(self, scoring_weights: ScoringWeights):
        service = self._build_service(scoring_weights)

        service.handle_contact_change(
            {
                "contact_id": "c-1",
                "event_type": "create",
                "user_ids": ["a-1"],
                "first_name": "Jane",
                "email": "jane@test.com",
                "price_min": 200000,
                "price_max": 500000,
                "zip_codes": ["90210"],
            }
        )

        saved = self.repo.contacts["c-1"]
        assert saved.score > 0  # profile signals computed
        assert saved.embedding_vector is not None
        assert AgentId("a-1") in self.flags.flagged

    def test_handle_update_preserves_score(self, scoring_weights: ScoringWeights):
        service = self._build_service(scoring_weights)

        # Seed existing contact with score
        existing = Contact(
            contact_id=ContactId("c-1"),
            user_ids=[AgentId("a-1")],
            score=50.0,
        )
        self.repo.save(existing)

        service.handle_contact_change(
            {
                "contact_id": "c-1",
                "event_type": "update",
                "user_ids": ["a-1"],
                "first_name": "Jane",
            }
        )

        saved = self.repo.contacts["c-1"]
        assert saved.score >= 50.0  # preserved + possibly added profile signals

    def test_handle_interaction(self, scoring_weights: ScoringWeights):
        service = self._build_service(scoring_weights)

        # Seed contact
        self.repo.save(
            Contact(
                contact_id=ContactId("c-1"),
                user_ids=[AgentId("a-1")],
            )
        )

        service.handle_interaction(
            {
                "contact_id": "c-1",
                "interaction_type": "listing_view",
                "detail": "Viewed listing l-1",
            }
        )

        saved = self.repo.contacts["c-1"]
        assert saved.score == 3.0

    def test_handle_interaction_contact_not_found(self, scoring_weights: ScoringWeights):
        service = self._build_service(scoring_weights)

        # Should not raise
        service.handle_interaction(
            {
                "contact_id": "c-999",
                "interaction_type": "listing_view",
            }
        )
