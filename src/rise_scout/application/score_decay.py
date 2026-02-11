from __future__ import annotations

import structlog

from rise_scout.domain.contact.repository import ContactRepository
from rise_scout.domain.scoring.decay import DecayCalculator

logger = structlog.get_logger()


class ScoreDecayService:
    def __init__(
        self,
        contact_repo: ContactRepository,
        decay_calculator: DecayCalculator,
    ) -> None:
        self._contact_repo = contact_repo
        self._decay_calculator = decay_calculator

    def run_decay(self) -> int:
        contacts = self._contact_repo.paginate_all()
        decayed = []

        for contact in contacts:
            if contact.score <= 0.0:
                continue
            self._decay_calculator.apply(contact)
            decayed.append(contact)

        self._contact_repo.bulk_save_batched(decayed)

        logger.info("decay_complete", total=len(contacts), decayed=len(decayed))
        return len(decayed)
