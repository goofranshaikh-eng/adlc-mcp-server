import logging
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

graphql_endpoint = os.getenv("GRAPHQL_ENDPOINT")
if not graphql_endpoint:
    logger.error("GRAPHQL_ENDPOINT environment variable is required")
    raise ValueError("GRAPHQL_ENDPOINT environment variable is required")

logger.info("Configured GraphQL endpoint: %s", graphql_endpoint)

mcp = FastMCP("MCP GraphQL Server")
# FastMCP 4 serves SSE with http_app(transport="sse"). No tools are registered yet.
mcp_app = mcp.http_app(path="/sse", transport="sse")

app = FastAPI(lifespan=mcp_app.lifespan)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"}, status_code=200)


app.mount("/", mcp_app)
