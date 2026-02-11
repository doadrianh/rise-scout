from __future__ import annotations

from typing import Protocol

from rise_scout.domain.contact.models import Contact
from rise_scout.domain.shared.types import AgentId, ContactId


class ContactRepository(Protocol):
    def get(self, contact_id: ContactId) -> Contact | None: ...

    def save(self, contact: Contact) -> None: ...

    def bulk_get(self, contact_ids: list[ContactId]) -> list[Contact]: ...

    def bulk_save(self, contacts: list[Contact]) -> None: ...

    def bulk_save_batched(self, contacts: list[Contact], batch_size: int = 100) -> None: ...

    def get_top_by_agents(
        self, agent_ids: list[AgentId], limit: int = 5
    ) -> dict[AgentId, list[Contact]]: ...

    def paginate_all(self, page_size: int = 500) -> list[Contact]: ...
