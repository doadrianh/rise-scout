from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import boto3
import structlog

from rise_scout.domain.cards.models import Card, CardContact
from rise_scout.domain.shared.types import AgentId, ContactId

logger = structlog.get_logger()


class DynamoDBCardRepository:
    def __init__(self, table_name: str, region: str = "us-west-2") -> None:
        self._table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def get(self, agent_id: AgentId) -> Card | None:
        resp = self._table.get_item(Key={"agent_id": str(agent_id)})
        item = resp.get("Item")
        if not item:
            return None
        return self._item_to_card(item)

    def save(self, card: Card) -> None:
        item = self._card_to_item(card)
        self._table.put_item(Item=item)
        logger.info("card_saved", agent_id=str(card.agent_id))

    def _card_to_item(self, card: Card) -> dict[str, Any]:
        expires_at = int(card.generated_at.timestamp()) + card.ttl
        return {
            "agent_id": str(card.agent_id),
            "contacts": json.dumps([c.model_dump(mode="json") for c in card.contacts]),
            "generated_at": card.generated_at.isoformat(),
            "ttl": card.ttl,
            "expires_at": expires_at,
        }

    def _item_to_card(self, item: dict[str, Any]) -> Card:
        contacts_data = json.loads(item["contacts"])
        contacts = [
            CardContact(
                contact_id=ContactId(c["contact_id"]),
                name=c["name"],
                score=c["score"],
                top_reasons=c.get("top_reasons", []),
                insight=c.get("insight", ""),
            )
            for c in contacts_data
        ]
        return Card(
            agent_id=AgentId(item["agent_id"]),
            contacts=contacts,
            generated_at=datetime.fromisoformat(item["generated_at"]).replace(tzinfo=UTC),
            ttl=int(item.get("ttl", 900)),
        )
