from __future__ import annotations

import json

import boto3
import structlog

from rise_scout.domain.contact.models import Contact

logger = structlog.get_logger()


class BedrockLLMService:
    def __init__(self, model_id: str, region: str = "us-west-2") -> None:
        self._client = boto3.client("bedrock-runtime", region_name=region)
        self._model_id = model_id

    def generate_insight(self, contact: Contact) -> str:
        reasons_text = "; ".join(
            f"{r.signal}: {r.detail} ({r.points:+.0f}pts)" for r in contact.score_reasons[:5]
        )

        prompt = (
            f"You are a real estate assistant. Given the following contact activity, "
            f"write a 1-2 sentence actionable insight for their agent.\n\n"
            f"Contact: {contact.first_name} {contact.last_name}\n"
            f"Score: {contact.score:.0f}\n"
            f"Recent signals: {reasons_text}\n\n"
            f"Insight:"
        )

        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 150,
                "messages": [{"role": "user", "content": prompt}],
            }
        )

        resp = self._client.invoke_model(modelId=self._model_id, body=body)
        result = json.loads(resp["body"].read())
        return result["content"][0]["text"].strip()
