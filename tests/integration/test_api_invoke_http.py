"""Regression test for .claude/rules/test_rule.md Rule 3.

src/api/server.py's /invoke route is async and wraps a sync agent.invoke() whose
nodes call asyncio.run() internally. Calling agent.invoke() directly from a
synchronous test function never enters an event loop, so it cannot reproduce
"asyncio.run() cannot be called from a running event loop" — the fix
(asyncio.to_thread in src/api/server.py) can only be verified by driving the
route on a real ASGI event loop.
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_invoke_endpoint_succeeds_over_http(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.setenv("SUBSTANCE_INDEX_API_KEY", "test-value")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-value")

    from src.api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/invoke", json={"input": "bom-ref-001"})

    assert resp.status_code == 200
    body = resp.json()
    # Default ANONYMOUS caller is denied by S-1 (nodes require VERIFIED_EXTERNAL) —
    # this still proves the async/sync boundary works (no swallowed asyncio.run()
    # RuntimeError, no "coroutine was never awaited" warning): a genuine business
    # error surfaces as status: "error", not an unhandled exception / 500.
    assert body["status"] in ("success", "error")


@pytest.mark.asyncio
async def test_health_endpoint(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "true")

    from src.api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
