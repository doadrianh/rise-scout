from __future__ import annotations

import base64
import json
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from rise_scout.application.contact_ingestion import ContactIngestionService
from rise_scout.infrastructure.container import Container

logger = Logger()
tracer = Tracer()

_container: Container | None = None


def _get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container


def _build_service(container: Container) -> ContactIngestionService:
    return ContactIngestionService(
        contact_repo=container.contact_repo,
        scoring_engine=container.scoring_engine,
        embedding_service=container.embedding_service,
        refresh_flags=container.refresh_flags,
        contact_parser=container.contact_change_parser,
        interaction_parser=container.interaction_parser,
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    container = _get_container()
    service = _build_service(container)
    processed = 0
    errors = 0

    for topic, records in event.get("records", {}).items():
        for record in records:
            try:
                raw = base64.b64decode(record["value"]).decode("utf-8")
                payload = json.loads(raw)

                if "ai_contact_change_payloads" in topic:
                    service.handle_contact_change(payload)
                elif "ai_contact_interactions" in topic:
                    service.handle_interaction(payload)
                else:
                    logger.warning("Unknown topic", topic=topic)
                    continue

                processed += 1
            except Exception:
                errors += 1
                logger.exception("Record processing failed", topic=topic)

    logger.info("Batch complete", processed=processed, errors=errors)
    return {"processed": processed, "errors": errors}
