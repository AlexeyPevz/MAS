import os
from fastapi.testclient import TestClient

os.environ["ENVIRONMENT"] = "testing"
os.environ["MAS_SECRET_KEY"] = "test-secret"
os.environ["ADMIN_SECRET"] = "test-admin-secret"

from api.main import app  # noqa: E402

client = TestClient(app)


def test_issue_token_and_ws_auth():
    # Issue token (admin)
    r = client.post(
        "/api/v1/auth/token",
        json={"user_id": "tester", "role": "admin"},
        headers={"X-Admin-Secret": "test-admin-secret"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Websocket with token
    with client.websocket_connect(f"/ws?token={token}") as ws:
        ws.send_text("ping")
        msg = ws.receive_text()
        assert msg == "pong"