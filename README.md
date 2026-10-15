# adlc-mcp-server

MCP server that exposes four tools for fetching sales order and employee data from a GraphQL service.

## Tools

| Tool | Description | Input |
|------|-------------|-------|
| `list_sales_order` | List all sales orders | none |
| `list_employees` | List all employees | none |
| `get_sales_order_by_id` | Fetch one sales order | `id` (string, required) |
| `get_employee_by_id` | Fetch one employee | `id` (string, required) |

Each tool returns a clear JSON success or error shape, for example:

- `{"salesOrders": [...]}` / `{"employees": [...]}`
- `{"salesOrder": {...}}` / `{"employee": {...}}` (or `null` when not found)
- `{"error": "<message>"}` on validation, network, or GraphQL failures

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GRAPHQL_ENDPOINT` | Yes | HTTP URL of the GraphQL service (e.g. `http://localhost:4000/graphql`) |

## Usage

Start the MCP server (stdio transport):

```bash
export GRAPHQL_ENDPOINT=http://localhost:4000/graphql
python -m mcp.server
```

Configure your MCP-compatible client to launch the same command with `GRAPHQL_ENDPOINT` set.

### Example tool results

```json
{"salesOrders": [{"id": "SO-001", "customerId": "C-123", "total": 1500.0, "status": "shipped"}]}
```

```json
{"employees": [{"id": "E-001", "name": "Alice Smith", "department": "Engineering", "email": "alice@example.com"}]}
```

```json
{"error": "Missing required parameter: id"}
```

## Tests

Unit tests (mocked GraphQL client, no external service):

```bash
pytest tests/ -k "not integration"
```

Integration tests (requires GraphQL service from PER-5):

```bash
export GRAPHQL_ENDPOINT=http://localhost:4000/graphql
pytest tests/test_mcp_server.py
```

All tests:

```bash
export GRAPHQL_ENDPOINT=http://localhost:4000/graphql
pytest tests/
```
