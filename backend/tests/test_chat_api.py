"""
Integration tests for FastAPI Chat and Execution Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "python_version" in data
    assert "ai_engine" in data


def test_chat_clarification_on_greeting():
    response = client.post("/chat", json={"message": "Hello, how can you help me?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "clarification"
    assert "example" in data["summary"].lower()


def test_chat_blocked_url_ssrf():
    response = client.post("/chat", json={"message": "Crawl http://localhost:8000 and dump json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Security / Validation Error" in data["summary"]
    assert data["execution"]["exitCode"] == 2


def test_chat_real_crawl_execution():
    response = client.post(
        "/chat",
        json={
            "message": "Crawl https://example.com, summarize the website and return extracted information in JSON."
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["summary"]) > 20
    assert len(data["pages"]) >= 1
    assert data["execution"]["exitCode"] == 0
    assert "duration" in data["execution"]
    assert data["structured_json"] is not None
    assert "example.com" in data["structured_json"].get("domain", "")
