from __future__ import annotations

import logging

import redis
import structlog

from rise_scout.domain.scoring.decay import DecayCalculator
from rise_scout.domain.scoring.engine import ScoringEngine
from rise_scout.infrastructure.bedrock.embedding_service import BedrockEmbeddingService
from rise_scout.infrastructure.bedrock.llm_service import BedrockLLMService
from rise_scout.infrastructure.config.weights_loader import load_weights
from rise_scout.infrastructure.dynamodb.card_repository import DynamoDBCardRepository
from rise_scout.infrastructure.kafka.parsers import (
    ContactChangeParser,
    InteractionParser,
    ListingParser,
)
from rise_scout.infrastructure.opensearch.client import create_aoss_client
from rise_scout.infrastructure.opensearch.contact_repository import OpenSearchContactRepository
from rise_scout.infrastructure.opensearch.search_repository import OpenSearchSearchRepository
from rise_scout.infrastructure.redis.debouncer import EventDebouncer
from rise_scout.infrastructure.redis.refresh_flags import RefreshFlagStore
from rise_scout.infrastructure.rise_api.client import StubRiseApiClient
from rise_scout.settings import Settings

logger = structlog.get_logger()


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self._init_logging()

        # Config
        self.weights = load_weights()
        self.scoring_engine = ScoringEngine(self.weights)
        self.decay_calculator = DecayCalculator(self.weights)

        # OpenSearch
        self._os_client = create_aoss_client(self.settings)
        self.contact_repo = OpenSearchContactRepository(
            self._os_client, self.settings.contacts_index
        )
        self.search_repo = OpenSearchSearchRepository(self._os_client, self.settings.contacts_index)

        # DynamoDB
        self.card_repo = DynamoDBCardRepository(self.settings.cards_table, self.settings.aws_region)

        # Redis
        self._redis_client = redis.from_url(self.settings.redis_url)
        self.refresh_flags = RefreshFlagStore(self._redis_client)
        self.debouncer = EventDebouncer(self._redis_client)

        # Bedrock
        self.embedding_service = BedrockEmbeddingService(
            self.settings.embedding_model_id, self.settings.aws_region
        )
        self.llm_service = BedrockLLMService(self.settings.llm_model_id, self.settings.aws_region)

        # Kafka parsers
        self.contact_change_parser = ContactChangeParser()
        self.interaction_parser = InteractionParser()
        self.listing_parser = ListingParser()

        # RISE API
        self.rise_api = StubRiseApiClient()

        logger.info("container_initialized", env=self.settings.env)

    def _init_logging(self) -> None:
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer()
                if self.settings.env == "dev"
                else structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                logging.DEBUG if self.settings.env == "dev" else logging.INFO
            ),
        )
