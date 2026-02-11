import pytest

from rise_scout.domain.contact.models import Contact, Preferences
from rise_scout.domain.scoring.decay import DecayCalculator
from rise_scout.domain.scoring.engine import ScoringEngine
from rise_scout.domain.scoring.signals import SignalType
from rise_scout.domain.shared.types import AgentId, ContactId
from rise_scout.infrastructure.config.weights_loader import load_weights


@pytest.mark.integration
class TestEndToEndScoringFlow:
    def test_full_scoring_lifecycle(self):
        weights = load_weights()
        engine = ScoringEngine(weights)
        decay = DecayCalculator(weights)

        contact = Contact(
            contact_id=ContactId("c-1"),
            user_ids=[AgentId("a-1"), AgentId("a-2")],
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="555-1234",
            preferences=Preferences(
                price_min=200000,
                price_max=500000,
                zip_codes=["90210"],
            ),
        )

        # Step 1: Profile signals
        profile_total = engine.compute_profile_signals(contact)
        # preferences_complete(15) + has_email(5) + has_phone(5) + multi_agent(10) = 35
        assert profile_total == 35.0
        assert contact.score == 35.0

        # Step 2: Engagement signals
        engine.process_signal(contact, SignalType.LISTING_VIEW, "Viewed l-1")
        engine.process_signal(contact, SignalType.LISTING_SAVE, "Saved l-1")
        assert contact.score == 46.0  # 35 + 3 + 8

        # Step 3: Market signal
        engine.process_signal(contact, SignalType.PRICE_DROP_MATCH, "l-1 dropped $20k")
        assert contact.score == 58.0  # 46 + 12

        # Step 4: Verify reasons accumulated
        assert len(contact.score_reasons) == 7  # 4 profile + 2 engagement + 1 market

        # Step 5: Apply decay
        pre_decay = contact.score
        decay.apply(contact)
        assert contact.score == pre_decay * 0.95
        assert contact.score < pre_decay

    def test_score_cap_enforced(self):
        weights = load_weights()
        engine = ScoringEngine(weights)

        contact = Contact(
            contact_id=ContactId("c-1"),
            user_ids=[AgentId("a-1")],
            score=990.0,
        )

        engine.process_signal(contact, SignalType.DOCUMENT_SIGNED, "signed")

        assert contact.score == 1000.0  # capped
