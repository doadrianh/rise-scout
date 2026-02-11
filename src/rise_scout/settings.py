from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "RISE_SCOUT_", "env_file": ".env"}

    env: str = "dev"
    aws_region: str = "us-west-2"

    # OpenSearch Serverless
    aoss_endpoint: str = ""
    contacts_index: str = "contacts"
    listings_index: str = "listings"

    # DynamoDB
    cards_table: str = "rise-scout-cards"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Bedrock
    embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    llm_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
