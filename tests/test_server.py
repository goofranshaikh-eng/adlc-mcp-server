import asyncio
import importlib
import os
import socket

import httpx
import pytest
import uvicorn

os.environ.setdefault("GRAPHQL_ENDPOINT", "https://example.com/graphql")

import server
from server import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify /health returns 200 + {"status": "ok"}."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_sse_endpoint_handshake():
    """Verify /sse FastMCP SSE handshake succeeds."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    running = uvicorn.Server(config)
    task = asyncio.create_task(running.serve())
    try:
        for _ in range(100):
            if running.started:
                break
            await asyncio.sleep(0.05)
        else:
            raise RuntimeError("uvicorn did not start")

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET",
                f"http://127.0.0.1:{port}/sse",
                headers={"Accept": "text/event-stream"},
                timeout=5.0,
            ) as response:
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")
                chunk = await asyncio.wait_for(response.aiter_text().__anext__(), timeout=3)
                assert "endpoint" in chunk
    finally:
        running.should_exit = True
        await asyncio.wait_for(task, timeout=5)


def test_server_startup_validation_missing_graphql_endpoint(monkeypatch, caplog):
    """Verify server fails to start if GRAPHQL_ENDPOINT is missing."""
    monkeypatch.delenv("GRAPHQL_ENDPOINT", raising=False)

    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError, match="GRAPHQL_ENDPOINT environment variable is required"):
            importlib.reload(server)

    assert "GRAPHQL_ENDPOINT environment variable is required" in caplog.text
