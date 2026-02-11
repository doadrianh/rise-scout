from __future__ import annotations

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from rise_scout.application.card_refresh import CardRefreshService
from rise_scout.infrastructure.container import Container

logger = Logger()
tracer = Tracer()

_container: Container | None = None


def _get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    container = _get_container()
    service = CardRefreshService(
        contact_repo=container.contact_repo,
        card_repo=container.card_repo,
        llm_service=container.llm_service,
        refresh_flags=container.refresh_flags,
    )

    refreshed = service.refresh_flagged_agents()
    logger.info("Card refresh complete", refreshed=refreshed)
    return {"refreshed": refreshed}
