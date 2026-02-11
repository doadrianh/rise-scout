from __future__ import annotations

from typing import Any, Protocol

from rise_scout.domain.contact.models import Contact
from rise_scout.domain.scoring.signals import SignalType
from rise_scout.domain.shared.types import ContactId


class ContactChangeParser(Protocol):
    def parse(self, payload: dict[str, Any]) -> tuple[Contact, bool]: ...


class InteractionParser(Protocol):
    def parse(self, payload: dict[str, Any]) -> tuple[ContactId, SignalType, str]: ...
