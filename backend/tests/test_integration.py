import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_NEO4J_TESTS") != "1",
    reason="Set RUN_NEO4J_TESTS=1 with Neo4j seeded",
)


def test_tcs_holders_include_rahul():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.post("/chat", json={"question": "Who owns TCS?"})
    assert r.status_code == 200
    data = r.json()
    assert "Rahul Sharma" in data["answer"]


def test_tcs_impact_rahul():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.post("/chat", json={"question": "What happens if TCS drops 10%?"})
    assert r.status_code == 200
    data = r.json()
    rahul = next((c for c in data["calculations"] if "Rahul" in c["label"]), None)
    assert rahul is not None
    assert rahul["value"] == -40000
