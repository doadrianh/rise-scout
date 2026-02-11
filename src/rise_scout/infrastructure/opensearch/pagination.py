from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import structlog
from opensearchpy import OpenSearch

logger = structlog.get_logger()


def search_after_paginator(
    client: OpenSearch,
    index: str,
    body: dict[str, Any],
    page_size: int = 500,
) -> Iterator[dict[str, Any]]:
    body["size"] = page_size
    body.setdefault("sort", [{"_id": "asc"}])

    search_after: list[Any] | None = None

    while True:
        if search_after is not None:
            body["search_after"] = search_after

        response = client.search(index=index, body=body)
        hits = response["hits"]["hits"]

        if not hits:
            break

        yield from hits

        search_after = hits[-1]["sort"]
        logger.debug("search_after_page", index=index, count=len(hits))
