from __future__ import annotations

from datetime import UTC, datetime, timedelta

from rise_scout.domain.contact.models import Contact
from rise_scout.domain.scoring.weights import ScoringWeights


class DecayCalculator:
    def __init__(self, weights: ScoringWeights) -> None:
        self._rate = weights.decay.rate
        self._retention_days = weights.decay.reason_retention_days

    def apply(self, contact: Contact) -> None:
        if contact.score <= 0.0:
            return

        contact.apply_decay(self._rate)
        self._prune_old_reasons(contact)

    def _prune_old_reasons(self, contact: Contact) -> None:
        cutoff = datetime.now(UTC) - timedelta(days=self._retention_days)
        contact.score_reasons = [r for r in contact.score_reasons if r.timestamp >= cutoff]
