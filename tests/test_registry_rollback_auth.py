import os
from fastapi.testclient import TestClient

os.environ["ENVIRONMENT"] = "testing"
os.environ["MAS_SECRET_KEY"] = "test-secret"
os.environ["ADMIN_SECRET"] = "test-admin-secret"

from api.main import app  # noqa: E402

client = TestClient(app)


def test_rollback_requires_admin():
    # No auth
    r = client.post("/api/v1/registry/tools/test/rollback")
    assert r.status_code == 403
    # User token
    r = client.post("/api/v1/auth/token", json={"user_id": "user", "role": "user"})
    token = r.json()["access_token"]
    r2 = client.post("/api/v1/registry/tools/test/rollback", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 403
    # Admin token
    r = client.post("/api/v1/auth/token", json={"user_id": "admin", "role": "admin"}, headers={"X-Admin-Secret": "test-admin-secret"})
    token = r.json()["access_token"]
    r3 = client.post("/api/v1/registry/tools/test/rollback", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code in (400, 404)