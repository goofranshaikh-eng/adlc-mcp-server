"""Tests 8–13: MCP tool success and error payloads with a mocked GraphQL client."""

import os
from unittest.mock import AsyncMock

import pytest

os.environ.setdefault("GRAPHQL_ENDPOINT", "https://example.com/graphql")

import server
from graphql_client import GraphQLClientError

SALES_ORDERS = [
    {
        "id": "SO-001",
        "accountName": "Acme Corp",
        "amount": 15000.0,
        "status": "Open",
    }
]

EMPLOYEES = [
    {
        "id": "EMP-001",
        "firstName": "Alice",
        "lastName": "Smith",
        "department": "Engineering",
        "email": "alice.smith@example.com",
    }
]

EMPLOYEES_OUT = [{**EMPLOYEES[0], "name": "Alice Smith"}]


def _payload(result) -> dict:
    if result.structured_content is not None:
        return result.structured_content
    raise AssertionError(f"tool result missing structured content: {result!r}")


@pytest.mark.asyncio
async def test_list_sales_order_returns_success_payload(monkeypatch):
    """Test 8: list_sales_order returns the sales-order list payload."""
    execute = AsyncMock(return_value={"salesorder_list": SALES_ORDERS})
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    result = await server.mcp.call_tool("list_sales_order")

    assert _payload(result) == {"salesOrders": SALES_ORDERS}
    execute.assert_awaited_once()
    query = execute.await_args.args[0]
    assert "ListSalesOrders" in query
    assert "salesorder_list" in query


@pytest.mark.asyncio
async def test_list_employees_returns_success_payload(monkeypatch):
    """Test 9: list_employees returns the employee list payload."""
    execute = AsyncMock(return_value={"employee_list": EMPLOYEES})
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    result = await server.mcp.call_tool("list_employees")

    assert _payload(result) == {"employees": EMPLOYEES_OUT}
    execute.assert_awaited_once()
    query = execute.await_args.args[0]
    assert "ListEmployees" in query
    assert "employee_list" in query


@pytest.mark.asyncio
async def test_get_sales_order_by_id_returns_success_payload(monkeypatch):
    """Test 10: get_sales_order_by_id returns the sales-order payload."""
    execute = AsyncMock(return_value={"get_salesorder_by_id": SALES_ORDERS[0]})
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    result = await server.mcp.call_tool("get_sales_order_by_id", {"id": "SO-001"})

    assert _payload(result) == {"salesOrder": SALES_ORDERS[0]}
    execute.assert_awaited_once()
    query = execute.await_args.args[0]
    variables = execute.await_args.args[1]
    assert "GetSalesOrderById" in query
    assert "get_salesorder_by_id" in query
    assert variables == {"id": "SO-001"}


@pytest.mark.asyncio
async def test_get_employee_by_id_returns_success_payload(monkeypatch):
    """Test 11: get_employee_by_id returns the employee payload."""
    execute = AsyncMock(return_value={"get_employee_by_id": EMPLOYEES[0]})
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    result = await server.mcp.call_tool("get_employee_by_id", {"id": "EMP-001"})

    assert _payload(result) == {"employee": EMPLOYEES_OUT[0]}
    execute.assert_awaited_once()
    query = execute.await_args.args[0]
    variables = execute.await_args.args[1]
    assert "GetEmployeeById" in query
    assert "get_employee_by_id" in query
    assert variables == {"id": "EMP-001"}


@pytest.mark.asyncio
async def test_get_sales_order_by_id_missing_id_returns_error(monkeypatch):
    """Test 12: missing or empty id returns an error payload and skips GraphQL."""
    execute = AsyncMock()
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    missing = await server.mcp.call_tool("get_sales_order_by_id", {})
    blank = await server.mcp.call_tool("get_sales_order_by_id", {"id": "  "})

    assert _payload(missing) == {"error": "Missing required parameter: id"}
    assert _payload(blank) == {"error": "Missing required parameter: id"}
    execute.assert_not_called()


@pytest.mark.asyncio
async def test_tool_returns_error_when_graphql_client_raises(monkeypatch):
    """Test 13: a GraphQL client exception becomes an error payload."""
    execute = AsyncMock(side_effect=GraphQLClientError("GraphQL endpoint unreachable"))
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    result = await server.mcp.call_tool("list_sales_order")

    assert _payload(result) == {"error": "GraphQL endpoint unreachable"}
