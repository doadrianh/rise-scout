from __future__ import annotations

import json

import boto3
import structlog

logger = structlog.get_logger()


class BedrockEmbeddingService:
    def __init__(self, model_id: str, region: str = "us-west-2") -> None:
        self._client = boto3.client("bedrock-runtime", region_name=region)
        self._model_id = model_id

    def embed(self, text: str) -> list[float]:
        body = json.dumps({"inputText": text})
        resp = self._client.invoke_model(modelId=self._model_id, body=body)
        result = json.loads(resp["body"].read())
        return result["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]
