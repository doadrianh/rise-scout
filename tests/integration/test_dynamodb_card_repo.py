import os

import boto3
import pytest
from moto import mock_aws

from rise_scout.domain.cards.models import Card, CardContact
from rise_scout.domain.shared.types import AgentId, ContactId
from rise_scout.infrastructure.dynamodb.card_repository import DynamoDBCardRepository


@pytest.fixture
def dynamodb_table():
    with mock_aws():
        os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"

        client = boto3.client("dynamodb", region_name="us-west-2")
        client.create_table(
            TableName="test-cards",
            KeySchema=[{"AttributeName": "agent_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "agent_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield


@pytest.mark.integration
class TestDynamoDBCardRepository:
    def test_save_and_get(self, dynamodb_table):
        with mock_aws():
            repo = DynamoDBCardRepository("test-cards", "us-west-2")

            card = Card(
                agent_id=AgentId("a-1"),
                contacts=[
                    CardContact(
                        contact_id=ContactId("c-1"),
                        name="Jane Doe",
                        score=42.5,
                        top_reasons=["Viewed listing", "Price drop"],
                        insight="Hot lead - actively searching",
                    )
                ],
            )

            repo.save(card)
            retrieved = repo.get(AgentId("a-1"))

            assert retrieved is not None
            assert str(retrieved.agent_id) == "a-1"
            assert len(retrieved.contacts) == 1
            assert retrieved.contacts[0].name == "Jane Doe"
            assert retrieved.contacts[0].score == 42.5
            assert retrieved.contacts[0].insight == "Hot lead - actively searching"

    def test_get_nonexistent(self, dynamodb_table):
        with mock_aws():
            repo = DynamoDBCardRepository("test-cards", "us-west-2")
            result = repo.get(AgentId("nonexistent"))
            assert result is None
