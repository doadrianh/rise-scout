from __future__ import annotations

from typing import Any

from rise_scout.domain.contact.models import Contact, Preferences, ScoreReason
from rise_scout.domain.shared.types import AgentId, ContactId, ListingId, MlsId


def contact_to_document(contact: Contact) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "contact_id": str(contact.contact_id),
        "user_ids": [str(uid) for uid in contact.user_ids],
        "organisationalunit_id": contact.organisationalunit_id,
        "mls_ids": [str(mid) for mid in contact.mls_ids],
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "email": contact.email,
        "phone": contact.phone,
        "preferences": contact.preferences.model_dump(),
        "watched_listings": [str(lid) for lid in contact.watched_listings],
        "score": contact.score,
        "score_reasons": [r.model_dump(mode="json") for r in contact.score_reasons],
        "last_interaction_at": (
            contact.last_interaction_at.isoformat() if contact.last_interaction_at else None
        ),
        "updated_at": contact.updated_at.isoformat(),
    }
    if contact.embedding_vector is not None:
        doc["embedding_vector"] = contact.embedding_vector
    return doc


def document_to_contact(doc: dict[str, Any]) -> Contact:
    kwargs: dict[str, Any] = {
        "contact_id": ContactId(doc["contact_id"]),
        "user_ids": [AgentId(uid) for uid in doc.get("user_ids", [])],
        "organisationalunit_id": doc.get("organisationalunit_id"),
        "mls_ids": [MlsId(mid) for mid in doc.get("mls_ids", [])],
        "first_name": doc.get("first_name", ""),
        "last_name": doc.get("last_name", ""),
        "email": doc.get("email"),
        "phone": doc.get("phone"),
        "preferences": Preferences.model_validate(doc.get("preferences", {})),
        "watched_listings": [ListingId(lid) for lid in doc.get("watched_listings", [])],
        "score": doc.get("score", 0.0),
        "score_reasons": [ScoreReason.model_validate(r) for r in doc.get("score_reasons", [])],
        "embedding_vector": doc.get("embedding_vector"),
        "last_interaction_at": doc.get("last_interaction_at"),
    }
    if "updated_at" in doc:
        kwargs["updated_at"] = doc["updated_at"]
    return Contact(**kwargs)
