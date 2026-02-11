from __future__ import annotations

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from rise_scout.settings import Settings


def create_aoss_client(settings: Settings) -> OpenSearch:
    credentials = boto3.Session().get_credentials()
    if credentials is None:
        raise RuntimeError("AWS credentials not found")
    auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        settings.aws_region,
        "aoss",
        session_token=credentials.token,
    )
    return OpenSearch(
        hosts=[{"host": settings.aoss_endpoint.replace("https://", ""), "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize=20,
    )
