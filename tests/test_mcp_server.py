"""Integration tests for MCP tools against a local GraphQL service."""

import os

import pytest

from mcp.graphql_client import GraphQLClient
from mcp.tools.list_employees import list_employees
from mcp.tools.list_sales_order import list_sales_order


def _require_endpoint() -> str:
    endpoint = os.getenv("GRAPHQL_ENDPOINT")
    if not endpoint:
        pytest.skip("GRAPHQL_ENDPOINT not set; skipping integration tests")
    return endpoint


def test_list_sales_order_integration():
    endpoint = _require_endpoint()
    client = GraphQLClient(endpoint)

    result = list_sales_order(client)

    assert "error" not in result
    assert "salesOrders" in result
    assert isinstance(result["salesOrders"], list)


def test_list_employees_integration():
    endpoint = _require_endpoint()
    client = GraphQLClient(endpoint)

    result = list_employees(client)

    assert "error" not in result
    assert "employees" in result
    assert isinstance(result["employees"], list)
