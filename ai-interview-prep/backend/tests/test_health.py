"""
tests/test_health.py — one real passing test that verifies GET /health → 200.
Run with:  pytest backend/tests/
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200_and_ok_status():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
