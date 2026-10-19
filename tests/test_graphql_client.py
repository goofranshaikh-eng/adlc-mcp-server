from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from graphql_client import GraphQLClient, GraphQLClientError

ENDPOINT = "https://example.com/graphql"
QUERY = "query { ping }"


def _mock_async_client(post_result=None, post_error=None):
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    if post_error is not None:
        mock_client.post.side_effect = post_error
    else:
        mock_client.post.return_value = post_result
    return mock_client


def _json_response(status_code: int, body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body
    return response


@pytest.mark.asyncio
async def test_successful_query_returns_data():
    """Test 4: a successful query returns the GraphQL data object."""
    payload = {"salesOrders": [{"id": "1"}]}
    response = _json_response(200, {"data": payload})
    mock_client = _mock_async_client(post_result=response)

    with patch("graphql_client.httpx.AsyncClient", return_value=mock_client) as async_client:
        client = GraphQLClient(endpoint=ENDPOINT)
        result = await client.execute(QUERY, {"limit": 1})

    assert result == payload
    async_client.assert_called_once_with(timeout=30.0)
    mock_client.post.assert_awaited_once_with(
        ENDPOINT,
        json={"query": QUERY, "variables": {"limit": 1}},
    )


@pytest.mark.asyncio
async def test_network_error_raises_exception():
    """Test 5: a network error raises a descriptive exception."""
    mock_client = _mock_async_client(post_error=httpx.ConnectError("connection refused"))

    with patch("graphql_client.httpx.AsyncClient", return_value=mock_client):
        client = GraphQLClient(endpoint=ENDPOINT)
        with pytest.raises(GraphQLClientError, match="GraphQL endpoint unreachable"):
            await client.execute(QUERY)


@pytest.mark.asyncio
async def test_graphql_errors_field_raises_exception():
    """Test 6: a GraphQL errors field raises a descriptive exception."""
    response = _json_response(
        200,
        {"data": None, "errors": [{"message": "Cannot query field 'nope'"}]},
    )
    mock_client = _mock_async_client(post_result=response)

    with patch("graphql_client.httpx.AsyncClient", return_value=mock_client):
        client = GraphQLClient(endpoint=ENDPOINT)
        with pytest.raises(
            GraphQLClientError,
            match=r"GraphQL returned error: Cannot query field 'nope'",
        ):
            await client.execute(QUERY)


@pytest.mark.asyncio
async def test_http_error_raises_exception():
    """Test 7: a non-2xx HTTP status raises a descriptive exception."""
    response = _json_response(503, {"errors": [{"message": "unavailable"}]})
    mock_client = _mock_async_client(post_result=response)

    with patch("graphql_client.httpx.AsyncClient", return_value=mock_client):
        client = GraphQLClient(endpoint=ENDPOINT)
        with pytest.raises(GraphQLClientError, match="GraphQL returned error: HTTP 503"):
            await client.execute(QUERY)


def test_missing_endpoint_raises_exception(monkeypatch):
    """A missing or empty endpoint fails before any request is sent."""
    monkeypatch.delenv("GRAPHQL_ENDPOINT", raising=False)

    with pytest.raises(ValueError, match="GRAPHQL_ENDPOINT environment variable is required"):
        GraphQLClient()

    with pytest.raises(ValueError, match="GRAPHQL_ENDPOINT environment variable is required"):
        GraphQLClient(endpoint="  ")
