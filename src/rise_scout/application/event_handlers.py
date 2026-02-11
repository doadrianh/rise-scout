from __future__ import annotations

from typing import Iterable

from rise_scout.domain.contact.models import Contact
from rise_scout.domain.shared.events import ContactScored
from rise_scout.domain.shared.services import RefreshFlagService
from rise_scout.domain.shared.types import AgentId


def dispatch_contact_events(
    contacts: Iterable[Contact],
    refresh_flags: RefreshFlagService,
) -> None:
    agent_ids: set[AgentId] = set()
    for contact in contacts:
        for event in contact.collect_events():
            if isinstance(event, ContactScored):
                agent_ids.update(event.agent_ids)
    if agent_ids:
        refresh_flags.flag_agents(list(agent_ids))
