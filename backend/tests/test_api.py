"""
Integration tests for API endpoints: Health, Sessions, Observe, Memory, Context, Graph.
"""
import pytest
from fastapi.testclient import TestClient
from main import application

client = TestClient(application)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_session_lifecycle():
    # 1. Create session
    create_res = client.post("/api/v1/sessions", json={"title": "Test Session"})
    assert create_res.status_code == 201
    session = create_res.json()
    session_id = session["id"]
    assert session["title"] == "Test Session"
    assert session["is_active"] is True

    # 2. Get session
    get_res = client.get(f"/api/v1/sessions/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == session_id


def test_observe_and_retrieve_flow():
    # 1. Create session
    create_res = client.post("/api/v1/sessions", json={"title": "Observe Test"})
    session_id = create_res.json()["id"]

    # 2. Observe input
    obs_res = client.post(
        "/api/v1/observe",
        json={"session_id": session_id, "text": "Alice lives in Berlin and works at Google on Python."},
    )
    assert obs_res.status_code == 200
    obs_data = obs_res.json()
    assert obs_data["session_id"] == session_id
    assert "reply" in obs_data
    assert len(obs_data["compiler_result"]["entities"]) >= 1

    # 3. Get graph
    graph_res = client.get(f"/api/v1/graph?session_id={session_id}")
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data

    # 4. Memory retrieval
    mem_res = client.get(f"/api/v1/memory?session_id={session_id}&query=Where does Alice live?")
    assert mem_res.status_code == 200
    mem_data = mem_res.json()
    assert len(mem_data["memories"]) >= 1

    # 5. Context compiler bundle
    ctx_res = client.get(f"/api/v1/context?session_id={session_id}&token_budget=1500")
    assert ctx_res.status_code == 200
    ctx_data = ctx_res.json()
    assert ctx_data["token_budget"] == 1500
    assert "context_text" in ctx_data

    # 6. Reason turn
    reason_res = client.post(
        "/api/v1/reason",
        json={"session_id": session_id, "query": "What language does Alice use?"},
    )
    assert reason_res.status_code == 200
    assert "response" in reason_res.json()
