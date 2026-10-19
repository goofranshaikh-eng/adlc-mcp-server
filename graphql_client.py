import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GraphQLClientError(Exception):
    """Raised when a GraphQL request cannot be completed."""


class GraphQLClient:
    """Async GraphQL executor backed by httpx."""

    def __init__(self, endpoint: str | None = None):
        resolved = endpoint if endpoint is not None else os.getenv("GRAPHQL_ENDPOINT")
        if resolved is None or not resolved.strip():
            raise ValueError("GRAPHQL_ENDPOINT environment variable is required")
        self.endpoint = resolved.strip()

    async def execute(self, query: str, variables: dict | None = None) -> dict:
        payload: dict[str, Any] = {"query": query, "variables": variables or {}}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.endpoint, json=payload)
        except httpx.RequestError as exc:
            logger.error("GraphQL endpoint unreachable")
            raise GraphQLClientError("GraphQL endpoint unreachable") from exc

        if response.status_code < 200 or response.status_code >= 300:
            message = f"GraphQL returned error: HTTP {response.status_code}"
            logger.error(message)
            raise GraphQLClientError(message)

        try:
            body = response.json()
        except ValueError as exc:
            message = "GraphQL returned error: invalid JSON response"
            logger.error(message)
            raise GraphQLClientError(message) from exc

        if not isinstance(body, dict):
            message = "GraphQL returned error: invalid JSON response"
            logger.error(message)
            raise GraphQLClientError(message)

        errors = body.get("errors")
        if errors:
            message = f"GraphQL returned error: {_format_graphql_errors(errors)}"
            logger.error(message)
            raise GraphQLClientError(message)

        data = body.get("data")
        if not isinstance(data, dict):
            message = "GraphQL returned error: response missing data"
            logger.error(message)
            raise GraphQLClientError(message)
        return data


def _format_graphql_errors(errors: object) -> str:
    if isinstance(errors, list):
        parts: list[str] = []
        for item in errors:
            if isinstance(item, dict) and item.get("message"):
                parts.append(str(item["message"]))
            else:
                parts.append(str(item))
        if parts:
            return "; ".join(parts)
    return str(errors)
