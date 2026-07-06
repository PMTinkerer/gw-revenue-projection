"""Happy-path + auth tests for the projection log API."""
import importlib
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

KEY = "test-key-123"

SAMPLE = {
    "address": "12 Shore Rd, Wells, ME",
    "label": "Ocean View Cottage",
    "bucket": "4br",
    "use_case": "owner_onboarding",
    "framework_version": "1.1",
    "inputs": {"peak_central": 1000, "booking_fee_pct": 10, "mgmt_rate_pct": 20},
    "outputs": {"totals": {"mid": 97909}},
    "notes": "sent 2026-07-06",
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PROJECTIONS_API_KEY", KEY)
    import app.main as main
    importlib.reload(main)
    with TestClient(main.app) as c:
        yield c


def auth():
    return {"Authorization": f"Bearer {KEY}"}


def test_healthz_needs_no_auth(client):
    assert client.get("/healthz").json() == {"ok": True}


def test_rejects_missing_or_wrong_key(client):
    assert client.get("/api/projections").status_code == 401
    bad = {"Authorization": "Bearer nope"}
    assert client.post("/api/projections", json=SAMPLE, headers=bad).status_code == 401


def test_save_list_get_delete_roundtrip(client):
    created = client.post("/api/projections", json=SAMPLE, headers=auth())
    assert created.status_code == 201
    pid = created.json()["id"]

    listed = client.get("/api/projections", params={"q": "Shore Rd"}, headers=auth())
    assert listed.status_code == 200
    assert [r["id"] for r in listed.json()] == [pid]
    assert listed.json()[0]["inputs"]["peak_central"] == 1000

    full = client.get(f"/api/projections/{pid}", headers=auth())
    assert full.status_code == 200
    assert full.json()["outputs"] == SAMPLE["outputs"]
    assert full.json()["address"] == SAMPLE["address"]

    assert client.delete(f"/api/projections/{pid}", headers=auth()).json() == {"deleted": True}
    assert client.get(f"/api/projections/{pid}", headers=auth()).status_code == 404


def test_address_required(client):
    bad = dict(SAMPLE, address="")
    assert client.post("/api/projections", json=bad, headers=auth()).status_code == 422
