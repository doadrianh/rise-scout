from __future__ import annotations

from typing import Protocol

from rise_scout.domain.contact.models import Contact


class LLMEnrichmentService(Protocol):
    def generate_insight(self, contact: Contact) -> str: ...
