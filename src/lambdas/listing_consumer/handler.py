from __future__ import annotations

import base64
import json
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from rise_scout.application.listing_matching import ListingMatchingService
from rise_scout.infrastructure.container import Container

logger = Logger()
tracer = Tracer()

_container: Container | None = None


def _get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container


def _build_service(container: Container) -> ListingMatchingService:
    return ListingMatchingService(
        contact_repo=container.contact_repo,
        search_repo=container.search_repo,
        scoring_engine=container.scoring_engine,
        refresh_flags=container.refresh_flags,
        listing_parser=container.listing_parser,
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    container = _get_container()
    service = _build_service(container)
    processed = 0
    errors = 0

    for _topic, records in event.get("records", {}).items():
        for record in records:
            try:
                raw = base64.b64decode(record["value"]).decode("utf-8")
                payload = json.loads(raw)
                service.handle_listing_event(payload)
                processed += 1
            except Exception:
                errors += 1
                logger.exception("Listing record failed")

    logger.info("Listing batch complete", processed=processed, errors=errors)
    return {"processed": processed, "errors": errors}
