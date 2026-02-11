from __future__ import annotations

from typing import Any

import structlog
from opensearchpy import OpenSearch

from rise_scout.domain.contact.models import Contact
from rise_scout.domain.shared.types import AgentId, ContactId
from rise_scout.infrastructure.opensearch.pagination import search_after_paginator
from rise_scout.infrastructure.opensearch.serializers import (
    contact_to_document,
    document_to_contact,
)

logger = structlog.get_logger()


class OpenSearchContactRepository:
    def __init__(self, client: OpenSearch, index: str) -> None:
        self._client = client
        self._index = index

    def get(self, contact_id: ContactId) -> Contact | None:
        try:
            resp = self._client.get(index=self._index, id=str(contact_id))
            return document_to_contact(resp["_source"])
        except Exception:
            logger.debug("contact_not_found", contact_id=str(contact_id))
            return None

    def save(self, contact: Contact) -> None:
        doc = contact_to_document(contact)
        self._client.index(
            index=self._index,
            id=str(contact.contact_id),
            body=doc,
        )
        logger.info("contact_saved", contact_id=str(contact.contact_id))

    def bulk_get(self, contact_ids: list[ContactId]) -> list[Contact]:
        if not contact_ids:
            return []

        resp = self._client.mget(
            index=self._index,
            body={"ids": [str(cid) for cid in contact_ids]},
        )
        contacts = []
        for doc in resp.get("docs", []):
            if doc.get("found"):
                contacts.append(document_to_contact(doc["_source"]))
        return contacts

    def bulk_save(self, contacts: list[Contact]) -> None:
        if not contacts:
            return

        actions: list[dict[str, Any]] = []
        for contact in contacts:
            actions.append({"index": {"_index": self._index, "_id": str(contact.contact_id)}})
            actions.append(contact_to_document(contact))

        resp = self._client.bulk(body=actions)
        if resp.get("errors"):
            failed = [item for item in resp["items"] if item["index"].get("error")]
            logger.error("bulk_save_errors", count=len(failed))
        else:
            logger.info("bulk_save_complete", count=len(contacts))

    def bulk_save_batched(self, contacts: list[Contact], batch_size: int = 100) -> None:
        for i in range(0, len(contacts), batch_size):
            self.bulk_save(contacts[i : i + batch_size])

    def get_top_by_agents(
        self, agent_ids: list[AgentId], limit: int = 5
    ) -> dict[AgentId, list[Contact]]:
        result: dict[AgentId, list[Contact]] = {}

        for agent_id in agent_ids:
            body: dict[str, Any] = {
                "query": {"term": {"user_ids": str(agent_id)}},
                "sort": [{"score": {"order": "desc"}}],
                "size": limit,
            }
            resp = self._client.search(index=self._index, body=body)
            contacts = [document_to_contact(hit["_source"]) for hit in resp["hits"]["hits"]]
            result[agent_id] = contacts

        return result

    def paginate_all(self, page_size: int = 500) -> list[Contact]:
        body: dict[str, Any] = {
            "query": {"match_all": {}},
            "sort": [{"_id": "asc"}],
        }
        contacts = []
        for hit in search_after_paginator(self._client, self._index, body, page_size):
            contacts.append(document_to_contact(hit["_source"]))
        return contacts
