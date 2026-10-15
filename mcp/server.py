"""MCP server entry point and tool registration."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path


def _load_sdk():
    """Load official MCP SDK classes, avoiding shadowing by this local ``mcp`` package."""
    repo_root = str(Path(__file__).resolve().parents[1])
    saved = {
        key: sys.modules.pop(key)
        for key in list(sys.modules)
        if key == "mcp" or key.startswith("mcp.")
    }
    removed = []
    cwd = os.getcwd()
    for entry in list(sys.path):
        absolute = os.path.abspath(entry if entry else cwd)
        if absolute == os.path.abspath(repo_root):
            removed.append(entry)
            sys.path.remove(entry)
    try:
        from mcp import types
        from mcp.server import Server
        from mcp.server.models import InitializationOptions
        from mcp.server.stdio import stdio_server

        sdk = {
            key: mod
            for key, mod in sys.modules.items()
            if key == "mcp" or key.startswith("mcp.")
        }
        return Server, types, InitializationOptions, stdio_server, sdk
    finally:
        for key in list(sys.modules):
            if key == "mcp" or key.startswith("mcp."):
                del sys.modules[key]
        for entry in removed:
            if entry not in sys.path:
                sys.path.insert(0, entry)
        sys.modules.update(saved)


def main() -> None:
    """
    MCP server entry point.

    Reads GRAPHQL_ENDPOINT from environment, initializes GraphQL client,
    registers all four tools, and starts the MCP server.

    Exits with status 1 if GRAPHQL_ENDPOINT is not set or client
    initialization fails.
    """
    logging.basicConfig(level=logging.INFO)

    endpoint = os.getenv("GRAPHQL_ENDPOINT")
    if not endpoint:
        logging.error("GRAPHQL_ENDPOINT environment variable not set")
        sys.exit(1)

    from mcp.graphql_client import GraphQLClient
    from mcp.tools.get_employee_by_id import get_employee_by_id
    from mcp.tools.get_sales_order_by_id import get_sales_order_by_id
    from mcp.tools.list_employees import list_employees
    from mcp.tools.list_sales_order import list_sales_order

    try:
        graphql_client = GraphQLClient(endpoint)
    except ValueError as exc:
        logging.error("Invalid GraphQL endpoint: %s", exc)
        sys.exit(1)

    Server, types, InitializationOptions, stdio_server, sdk_modules = _load_sdk()

    server = Server("mcp-graphql-server")

    @server.list_tools()
    async def handle_list_tools() -> list:
        return [
            types.Tool(
                name="list_sales_order",
                description="Query GraphQL service for all sales orders",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="list_employees",
                description="Query GraphQL service for all employees",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="get_sales_order_by_id",
                description="Query GraphQL service for a sales order by ID",
                inputSchema={
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"],
                },
            ),
            types.Tool(
                name="get_employee_by_id",
                description="Query GraphQL service for an employee by ID",
                inputSchema={
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict | None) -> list:
        arguments = arguments or {}
        if name == "list_sales_order":
            result = list_sales_order(graphql_client)
        elif name == "list_employees":
            result = list_employees(graphql_client)
        elif name == "get_sales_order_by_id":
            result = get_sales_order_by_id(graphql_client, arguments.get("id"))
        elif name == "get_employee_by_id":
            result = get_employee_by_id(graphql_client, arguments.get("id"))
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [types.TextContent(type="text", text=json.dumps(result))]

    async def run() -> None:
        local = {
            key: sys.modules.pop(key)
            for key in list(sys.modules)
            if key == "mcp" or key.startswith("mcp.")
        }
        sys.modules.update(sdk_modules)
        try:
            init_options: InitializationOptions = server.create_initialization_options()
            async with stdio_server() as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    init_options,
                )
        finally:
            for key in list(sys.modules):
                if key == "mcp" or key.startswith("mcp."):
                    del sys.modules[key]
            sys.modules.update(local)

    asyncio.run(run())


if __name__ == "__main__":
    main()
