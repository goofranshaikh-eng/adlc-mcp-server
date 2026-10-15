"""Unit tests for GraphQL client."""

from unittest.mock import MagicMock, patch

import pytest

from mcp.graphql_client import GraphQLClient, NetworkError


def test_execute_query_success():
    client = GraphQLClient("http://example.com/graphql")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {"salesOrders": [{"id": "SO-001"}]},
        "errors": None,
    }

    with patch("mcp.graphql_client.requests.post", return_value=mock_response) as post:
        data, errors = client.execute_query("{ salesOrders { id } }")

    assert data == {"salesOrders": [{"id": "SO-001"}]}
    assert errors == []
    post.assert_called_once()
    assert post.call_args.kwargs["headers"]["Content-Type"] == "application/json"


def test_execute_query_http_error():
    client = GraphQLClient("http://example.com/graphql")
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("mcp.graphql_client.requests.post", return_value=mock_response):
        data, errors = client.execute_query("{ salesOrders { id } }")

    assert data is None
    assert errors == [{"message": "HTTP error: 500"}]


def test_execute_query_network_error():
    import requests

    client = GraphQLClient("http://example.com/graphql")

    with patch(
        "mcp.graphql_client.requests.post",
        side_effect=requests.ConnectionError("connection refused"),
    ):
        with pytest.raises(NetworkError, match="connection refused"):
            client.execute_query("{ salesOrders { id } }")


def test_execute_query_malformed_json():
    client = GraphQLClient("http://example.com/graphql")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("No JSON object could be decoded")

    with patch("mcp.graphql_client.requests.post", return_value=mock_response):
        with pytest.raises(ValueError, match="malformed JSON"):
            client.execute_query("{ salesOrders { id } }")
