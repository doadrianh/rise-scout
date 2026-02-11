from __future__ import annotations

from rise_scout.domain.contact.models import Contact, ScoreReason
from rise_scout.domain.scoring.signals import SignalType
from rise_scout.domain.scoring.weights import ScoringWeights


class ScoringEngine:
    def __init__(self, weights: ScoringWeights) -> None:
        self._weights = weights

    def process_signal(self, contact: Contact, signal: SignalType, detail: str = "") -> float:
        points = self._weights.signals.get(signal.value, 0.0)
        if points == 0.0:
            return 0.0

        reason = ScoreReason(
            signal=signal.value,
            points=points,
            category=signal.category,
            detail=detail,
        )
        contact.apply_score_delta(points, reason)
        contact.score = min(contact.score, self._weights.score_cap)
        return points

    def compute_profile_signals(self, contact: Contact) -> float:
        total = 0.0

        if contact.preferences.is_complete:
            total += self.process_signal(
                contact, SignalType.PREFERENCES_COMPLETE, "All required preferences set"
            )

        if contact.email:
            total += self.process_signal(contact, SignalType.HAS_EMAIL, contact.email)

        if contact.phone:
            total += self.process_signal(contact, SignalType.HAS_PHONE, contact.phone)

        if len(contact.user_ids) > 1:
            total += self.process_signal(
                contact,
                SignalType.MULTI_AGENT,
                f"{len(contact.user_ids)} agents",
            )

        return total
