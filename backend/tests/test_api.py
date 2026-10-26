from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["app"] == "Cloud CostPilot"


def test_register_login_me():
    get_settings.cache_clear()
    email = "demo@example.com"
    password = "secret12"
    r = client.post("/auth/register", json={"email": email, "password": password, "name": "Demo"})
    # re-register may fail if prior run; login instead
    if r.status_code == 400:
        r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    token = r.json()["token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == email


def test_resources_requires_auth():
    assert client.get("/resources").status_code == 401