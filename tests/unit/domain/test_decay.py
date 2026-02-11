from datetime import UTC, datetime, timedelta

from rise_scout.domain.contact.models import Contact, ScoreReason
from rise_scout.domain.scoring.decay import DecayCalculator
from rise_scout.domain.scoring.weights import DecayConfig, ScoringWeights
from rise_scout.domain.shared.types import AgentId, ContactId


def _make_contact(**kwargs):
    defaults = {
        "contact_id": ContactId("c-1"),
        "user_ids": [AgentId("a-1")],
    }
    defaults.update(kwargs)
    return Contact(**defaults)


def _make_reason(days_ago=0, signal="listing_view"):
    ts = datetime.now(UTC) - timedelta(days=days_ago)
    return ScoreReason(
        signal=signal, points=5.0, category="engagement", detail="test", timestamp=ts
    )


class TestDecayCalculator:
    def test_applies_decay_rate(self, scoring_weights: ScoringWeights):
        calc = DecayCalculator(scoring_weights)
        contact = _make_contact(score=100.0)

        calc.apply(contact)

        assert contact.score == 95.0

    def test_skips_zero_score(self, scoring_weights: ScoringWeights):
        calc = DecayCalculator(scoring_weights)
        contact = _make_contact(score=0.0)

        calc.apply(contact)

        assert contact.score == 0.0

    def test_floor_at_zero(self):
        weights = ScoringWeights(decay=DecayConfig(rate=0.0, reason_retention_days=30))
        calc = DecayCalculator(weights)
        contact = _make_contact(score=50.0)

        calc.apply(contact)

        assert contact.score == 0.0

    def test_prunes_old_reasons(self, scoring_weights: ScoringWeights):
        calc = DecayCalculator(scoring_weights)
        recent = _make_reason(days_ago=5)
        old = _make_reason(days_ago=45)
        contact = _make_contact(score=100.0, score_reasons=[recent, old])

        calc.apply(contact)

        assert len(contact.score_reasons) == 1
        assert contact.score_reasons[0] is recent

    def test_repeated_decay_converges_to_zero(self, scoring_weights: ScoringWeights):
        calc = DecayCalculator(scoring_weights)
        contact = _make_contact(score=100.0)

        for _ in range(200):
            calc.apply(contact)

        assert contact.score < 0.01

    def test_decay_math_correctness(self):
        weights = ScoringWeights(decay=DecayConfig(rate=0.5, reason_retention_days=30))
        calc = DecayCalculator(weights)
        contact = _make_contact(score=100.0)

        calc.apply(contact)
        assert contact.score == 50.0

        calc.apply(contact)
        assert contact.score == 25.0
