"""Tests 14–20: tools and health over the ASGI app with mocked GraphQL."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import httpx
import httpx2
import pytest
from fastmcp import Client
from fastmcp.client.transports import SSETransport
from fastmcp.utilities.asgi_transport import StreamingASGITransport, run_asgi_lifespan

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
    data = result.structured_content
    if data is None:
        data = result.data
    if isinstance(data, dict):
        return data
    raise AssertionError(f"tool result missing structured content: {result!r}")


def _asgi_http_client(
    headers: dict[str, str] | None = None,
    timeout: httpx2.Timeout | None = None,
    auth: httpx2.Auth | None = None,
) -> httpx2.AsyncClient:
    """httpx client that drives the FastAPI app in-process, including its SSE mount."""
    return httpx2.AsyncClient(
        transport=StreamingASGITransport(server.app, cancel_on_close=False),
        base_url="http://127.0.0.1",
        headers=headers,
        timeout=timeout,
        auth=auth,
    )


@asynccontextmanager
async def _mcp_client() -> AsyncIterator[Client]:
    """FastMCP client connected to the app's /sse endpoint without a live socket."""
    transport = SSETransport(
        "http://127.0.0.1/sse",
        httpx_client_factory=_asgi_http_client,
    )
    async with run_asgi_lifespan(server.app), Client(transport) as client:
        yield client


@pytest.mark.asyncio
async def test_list_sales_order_over_http(monkeypatch):
    """Test 14: list_sales_order succeeds over the app MCP stack."""
    execute = AsyncMock(return_value={"salesorder_list": SALES_ORDERS})
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    async with _mcp_client() as client:
        result = await client.call_tool("list_sales_order")

    assert _payload(result) == {"salesOrders": SALES_ORDERS}
    execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_employees_over_http(monkeypatch):
    """Test 15: list_employees succeeds over the app MCP stack."""
    execute = AsyncMock(return_value={"employee_list": EMPLOYEES})
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    async with _mcp_client() as client:
        result = await client.call_tool("list_employees")

    assert _payload(result) == {"employees": EMPLOYEES_OUT}
    execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_sales_order_by_id_over_http(monkeypatch):
    """Test 16: get_sales_order_by_id succeeds over the app MCP stack."""
    execute = AsyncMock(return_value={"get_salesorder_by_id": SALES_ORDERS[0]})
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    async with _mcp_client() as client:
        result = await client.call_tool("get_sales_order_by_id", {"id": "SO-001"})

    assert _payload(result) == {"salesOrder": SALES_ORDERS[0]}
    execute.assert_awaited_once()
    assert execute.await_args.args[1] == {"id": "SO-001"}


@pytest.mark.asyncio
async def test_get_employee_by_id_over_http(monkeypatch):
    """Test 17: get_employee_by_id succeeds over the app MCP stack."""
    execute = AsyncMock(return_value={"get_employee_by_id": EMPLOYEES[0]})
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    async with _mcp_client() as client:
        result = await client.call_tool("get_employee_by_id", {"id": "EMP-001"})

    assert _payload(result) == {"employee": EMPLOYEES_OUT[0]}
    execute.assert_awaited_once()
    assert execute.await_args.args[1] == {"id": "EMP-001"}


@pytest.mark.asyncio
async def test_graphql_error_returns_error_json_and_server_stays_up(monkeypatch):
    """Test 18: a GraphQL failure is error JSON and the app keeps serving."""
    execute = AsyncMock(
        side_effect=[
            GraphQLClientError("GraphQL endpoint unreachable"),
            {"employee_list": EMPLOYEES},
        ]
    )
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    async with _mcp_client() as client:
        failed = await client.call_tool("list_sales_order")
        assert _payload(failed) == {"error": "GraphQL endpoint unreachable"}

        recovered = await client.call_tool("list_employees")
        assert _payload(recovered) == {"employees": EMPLOYEES_OUT}

        async with _asgi_http_client() as http:
            health = await http.get("/health")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test 19: /health returns 200 and {"status": "ok"}."""
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_empty_id_returns_error_json(monkeypatch):
    """Test 20: an empty id is an error payload and does not call GraphQL."""
    execute = AsyncMock()
    monkeypatch.setattr(server.graphql_client, "execute", execute)

    async with _mcp_client() as client:
        result = await client.call_tool("get_sales_order_by_id", {"id": ""})

    assert _payload(result) == {"error": "Missing required parameter: id"}
    execute.assert_not_called()
