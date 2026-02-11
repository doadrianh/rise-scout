from datetime import UTC, datetime

from rise_scout.domain.contact.models import Contact, Preferences, ScoreReason
from rise_scout.domain.shared.types import AgentId, ContactId, ListingId, MlsId
from rise_scout.infrastructure.opensearch.serializers import (
    contact_to_document,
    document_to_contact,
)


def _make_contact():
    return Contact(
        contact_id=ContactId("c-1"),
        user_ids=[AgentId("a-1"), AgentId("a-2")],
        organisationalunit_id="org-1",
        mls_ids=[MlsId("mls-1")],
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        phone="555-1234",
        preferences=Preferences(
            price_min=200000,
            price_max=500000,
            beds_min=2,
            beds_max=4,
            zip_codes=["90210"],
            cities=["Beverly Hills"],
        ),
        watched_listings=[ListingId("l-1")],
        score=42.5,
        score_reasons=[
            ScoreReason(
                signal="listing_view",
                points=3.0,
                category="engagement",
                detail="Viewed listing l-1",
                timestamp=datetime(2024, 6, 1, tzinfo=UTC),
            )
        ],
        embedding_vector=[0.1, 0.2, 0.3],
        updated_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC),
    )


class TestSerializerRoundTrip:
    def test_round_trip_preserves_data(self):
        original = _make_contact()
        doc = contact_to_document(original)
        restored = document_to_contact(doc)

        assert restored.contact_id == original.contact_id
        assert restored.user_ids == original.user_ids
        assert restored.organisationalunit_id == original.organisationalunit_id
        assert restored.mls_ids == original.mls_ids
        assert restored.first_name == original.first_name
        assert restored.last_name == original.last_name
        assert restored.email == original.email
        assert restored.phone == original.phone
        assert restored.score == original.score
        assert len(restored.score_reasons) == 1
        assert restored.score_reasons[0].signal == "listing_view"
        assert restored.preferences.price_min == 200000
        assert restored.preferences.zip_codes == ["90210"]
        assert restored.watched_listings == original.watched_listings
        assert restored.embedding_vector == [0.1, 0.2, 0.3]

    def test_round_trip_no_embedding(self):
        original = _make_contact()
        original.embedding_vector = None
        doc = contact_to_document(original)

        assert "embedding_vector" not in doc

        restored = document_to_contact(doc)
        assert restored.embedding_vector is None

    def test_document_has_expected_keys(self):
        contact = _make_contact()
        doc = contact_to_document(contact)

        assert doc["contact_id"] == "c-1"
        assert doc["user_ids"] == ["a-1", "a-2"]
        assert doc["score"] == 42.5
        assert isinstance(doc["score_reasons"], list)
        assert isinstance(doc["preferences"], dict)
