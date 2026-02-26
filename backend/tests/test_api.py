"""API contract tests."""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Use temp DB for tests
_tmp = tempfile.mktemp(suffix=".db")
os.environ["DB_PATH"] = _tmp

from app.main import app
from app.database import init_db

init_db()

client = TestClient(app)


class TestHealth:
    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestProfile:
    def test_get_default_profile(self):
        r = client.get("/v1/user/profile")
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == "default"
        assert data["posted_within"] == "7d"

    def test_update_profile(self):
        r = client.put("/v1/user/profile", json={"track": "Backend", "posted_within": "24h"})
        assert r.status_code == 200
        assert r.json()["track"] == "Backend"
        assert r.json()["posted_within"] == "24h"


class TestSeeds:
    def test_create_and_list_seeds(self):
        r = client.post("/v1/seeds", json={
            "provider": "greenhouse",
            "company": "TestCo",
            "board_url": "https://boards.greenhouse.io/testco",
        })
        assert r.status_code == 201
        seed = r.json()
        assert seed["provider"] == "greenhouse"
        assert seed["company"] == "TestCo"
        assert "id" in seed

        r = client.get("/v1/seeds")
        assert r.status_code == 200
        seeds = r.json()
        assert any(s["id"] == seed["id"] for s in seeds)

    def test_delete_seed(self):
        r = client.post("/v1/seeds", json={
            "provider": "lever",
            "company": "DelCo",
            "board_url": "https://jobs.lever.co/delco",
        })
        seed_id = r.json()["id"]

        r = client.delete(f"/v1/seeds/{seed_id}")
        assert r.status_code == 204

        r = client.get("/v1/seeds")
        assert not any(s["id"] == seed_id for s in r.json())

    def test_delete_nonexistent_seed(self):
        r = client.delete("/v1/seeds/nonexistent")
        assert r.status_code == 404


class TestSearchRuns:
    def test_search_run_requires_seeds(self):
        # Remove all seeds first
        seeds = client.get("/v1/seeds").json()
        for s in seeds:
            client.delete(f"/v1/seeds/{s['id']}")

        r = client.post("/v1/search/runs", json={
            "track": "Backend",
            "posted_within": "7d",
            "provider_enabled": {"greenhouse": True, "lever": True},
            "limit_per_provider": 10,
        })
        assert r.status_code == 400
        assert "seeds" in r.json()["detail"].lower()


class TestQueue:
    def test_add_nonexistent_job_to_queue(self):
        r = client.post("/v1/queue/items", json={
            "job_id": "nonexistent-job-id",
        })
        assert r.status_code == 404

    def test_queue_list_empty(self):
        r = client.get("/v1/queue/items")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
