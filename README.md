# adlc-mcp-server

HTTP MCP server for TriNet GraphQL (sales orders and employees). FastAPI hosts the app and FastMCP serves tools over SSE. That HTTP path is how you run this server.

## Quick start

### Environment

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `GRAPHQL_ENDPOINT` | yes | — | GraphQL HTTP endpoint the tools query |
| `HOST` | no | `0.0.0.0` | Bind address used by `python main.py` |
| `PORT` | no | `8000` | Listen port used by `python main.py` |

Startup fails if `GRAPHQL_ENDPOINT` is missing.

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
export GRAPHQL_ENDPOINT=https://example.com/graphql
uvicorn server:app --host 0.0.0.0 --port 8000
```

`python main.py` starts the same app and reads optional `HOST` and `PORT`:

```bash
export GRAPHQL_ENDPOINT=https://example.com/graphql
python main.py
```

### MCP URL

Point HTTP MCP clients at:

```text
http://localhost:8000/sse
```

`GET http://localhost:8000/health` returns `{"status": "ok"}`.

Tool names and payloads match the previous stdio server:

- `list_sales_order`
- `list_employees`
- `get_sales_order_by_id` (`id`)
- `get_employee_by_id` (`id`)

## Migrating from stdio to HTTP

Earlier clients launched this server as a local process and spoke MCP over stdin/stdout (`command` and `args` in the client config).

v1 is a long-running HTTP server. Clients connect to the SSE URL and use the same tool names and arguments.

1. Set `GRAPHQL_ENDPOINT` on the server process (and `HOST` / `PORT` when you use `python main.py`).
2. Start the server with `uvicorn server:app --host 0.0.0.0 --port 8000` or `python main.py`.
3. Replace the stdio launch entry with an HTTP server entry whose URL is `http://localhost:8000/sse`.

```json
{
  "mcpServers": {
    "adlc-mcp-server": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Authentication

Authentication is deferred and out of scope for v1. The HTTP endpoint is open on the network it binds to. A later change will add auth; until then, run the server only where that exposure is acceptable.
