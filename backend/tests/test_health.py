"""Health endpoint and app startup tests."""

import pytest


@pytest.mark.asyncio
async def test_health_ok(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_unknown_route_returns_404(client):
    resp = await client.get("/api/v1/nonexistent")
    assert resp.status_code == 404
