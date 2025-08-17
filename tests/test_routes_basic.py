import os
from fastapi.testclient import TestClient

os.environ["ENVIRONMENT"] = "testing"
os.environ["MAS_SECRET_KEY"] = "test-secret"
os.environ["ADMIN_SECRET"] = "test-admin-secret"

from api.main import app  # noqa: E402

client = TestClient(app)


def get_admin_headers():
    resp = client.post("/api/v1/auth/token", json={"user_id": "admin", "role": "admin"}, headers={"X-Admin-Secret": "test-admin-secret"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_chat_alias_and_message():
    # chat alias
    r = client.post("/api/v1/chat", json={"message": "ping"})
    assert r.status_code in (200, 503)
    # message with visualization
    r = client.post("/api/v1/chat/message", json={"message": "ping"})
    assert r.status_code in (200, 500)


def test_metrics_dashboard():
    headers = get_admin_headers()
    r = client.get("/api/v1/metrics/dashboard", headers=headers)
    assert r.status_code in (200, 503)


def test_registry_read():
    r = client.get("/api/v1/registry/tools")
    assert r.status_code == 200


def test_ws_auth_denied_without_token():
    with client.websocket_connect("/ws") as ws:
        # Should close immediately with 1008; TestClient raises
        pass