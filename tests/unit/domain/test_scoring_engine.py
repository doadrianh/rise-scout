import pytest

from rise_scout.domain.contact.models import Contact, Preferences
from rise_scout.domain.scoring.engine import ScoringEngine
from rise_scout.domain.scoring.signals import SignalType
from rise_scout.domain.scoring.weights import ScoringWeights
from rise_scout.domain.shared.types import AgentId, ContactId


def _make_contact(**kwargs):
    defaults = {
        "contact_id": ContactId("c-1"),
        "user_ids": [AgentId("a-1")],
        "first_name": "Jane",
        "last_name": "Doe",
    }
    defaults.update(kwargs)
    return Contact(**defaults)


class TestScoringEngine:
    def test_process_signal_adds_correct_points(self, scoring_weights: ScoringWeights):
        engine = ScoringEngine(scoring_weights)
        contact = _make_contact()

        delta = engine.process_signal(contact, SignalType.LISTING_VIEW, "viewed listing 123")

        assert delta == 3.0
        assert contact.score == 3.0
        assert len(contact.score_reasons) == 1
        assert contact.score_reasons[0].signal == "listing_view"
        assert contact.score_reasons[0].category == "engagement"

    @pytest.mark.parametrize(
        "signal,expected_points",
        [
            (SignalType.PREFERENCES_COMPLETE, 15.0),
            (SignalType.HAS_EMAIL, 5.0),
            (SignalType.HAS_PHONE, 5.0),
            (SignalType.MULTI_AGENT, 10.0),
            (SignalType.LISTING_VIEW, 3.0),
            (SignalType.LISTING_SAVE, 8.0),
            (SignalType.LISTING_SHARE, 10.0),
            (SignalType.SEARCH_PERFORMED, 2.0),
            (SignalType.OPEN_HOUSE_RSVP, 20.0),
            (SignalType.DOCUMENT_SIGNED, 25.0),
            (SignalType.PRICE_DROP_MATCH, 12.0),
            (SignalType.NEW_LISTING_MATCH, 10.0),
            (SignalType.STATUS_CHANGE_MATCH, 8.0),
            (SignalType.BACK_ON_MARKET_MATCH, 15.0),
            (SignalType.AGENT_NOTE_ADDED, 5.0),
            (SignalType.CONTACTED_RECENTLY, 7.0),
        ],
    )
    def test_all_signals_produce_correct_points(
        self, scoring_weights: ScoringWeights, signal: SignalType, expected_points: float
    ):
        engine = ScoringEngine(scoring_weights)
        contact = _make_contact()

        delta = engine.process_signal(contact, signal, "test")

        assert delta == expected_points
        assert contact.score == expected_points

    def test_score_capped_at_max(self, scoring_weights: ScoringWeights):
        engine = ScoringEngine(scoring_weights)
        contact = _make_contact(score=990.0)

        engine.process_signal(contact, SignalType.DOCUMENT_SIGNED, "signed")

        assert contact.score == 1000.0

    def test_unknown_signal_returns_zero(self):
        engine = ScoringEngine(ScoringWeights(signals={}))
        contact = _make_contact()

        delta = engine.process_signal(contact, SignalType.LISTING_VIEW, "test")

        assert delta == 0.0
        assert contact.score == 0.0

    def test_compute_profile_signals_complete_contact(self, scoring_weights: ScoringWeights):
        engine = ScoringEngine(scoring_weights)
        contact = _make_contact(
            user_ids=[AgentId("a-1"), AgentId("a-2")],
            email="jane@example.com",
            phone="555-1234",
            preferences=Preferences(price_min=200000, price_max=500000, zip_codes=["90210"]),
        )

        total = engine.compute_profile_signals(contact)

        # preferences_complete(15) + has_email(5) + has_phone(5) + multi_agent(10) = 35
        assert total == 35.0
        assert contact.score == 35.0

    def test_compute_profile_signals_minimal_contact(self, scoring_weights: ScoringWeights):
        engine = ScoringEngine(scoring_weights)
        contact = _make_contact()

        total = engine.compute_profile_signals(contact)

        assert total == 0.0

    def test_compute_profile_email_only(self, scoring_weights: ScoringWeights):
        engine = ScoringEngine(scoring_weights)
        contact = _make_contact(email="jane@example.com")

        total = engine.compute_profile_signals(contact)

        assert total == 5.0
