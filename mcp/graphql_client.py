"""GraphQL HTTP client abstraction."""

from __future__ import annotations

import json
from typing import Any

import requests


class NetworkError(Exception):
    """Raised when network communication fails."""

    pass


class GraphQLClient:
    def __init__(self, endpoint: str):
        """
        Initialize client with GraphQL endpoint URL.

        Args:
            endpoint: GraphQL service HTTP endpoint URL

        Raises:
            ValueError: if endpoint is empty or None
        """
        if endpoint is None or not str(endpoint).strip():
            raise ValueError("endpoint must be a non-empty string")
        self.endpoint = str(endpoint).strip()

    def execute_query(
        self, query: str, variables: dict | None = None
    ) -> tuple[dict | None, list]:
        """
        Send GraphQL query via HTTP POST.

        Args:
            query: GraphQL query string
            variables: Optional query variables dict

        Returns:
            Tuple (data, errors) where:
            - data: Response data dict or None
            - errors: List of error dicts or empty list

        Raises:
            NetworkError: if HTTP request fails (connection refused, timeout)
            ValueError: if response JSON is malformed
        """
        payload: dict[str, Any] = {"query": query}
        if variables is not None:
            payload["variables"] = variables

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise NetworkError(str(exc)) from exc

        if response.status_code >= 400:
            return None, [{"message": f"HTTP error: {response.status_code}"}]

        try:
            body = response.json()
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"malformed JSON response: {exc}") from exc

        if not isinstance(body, dict):
            raise ValueError("malformed JSON response: expected object")

        data = body.get("data")
        errors = body.get("errors") or []
        if not isinstance(errors, list):
            errors = [{"message": str(errors)}]

        return data, errors
