import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_root():
    """Test the root endpoint /"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_health_check_health():
    """Test the /health endpoint"""
    # Note: This might fail if ChromaDB is not connected in the test environment
    # In a real CI/CD, we'd mock the rag pipeline or use a test container
    response = client.get("/health")
    assert response.status_code in [200, 503]
    assert "status" in response.json()

def test_ask_empty_question():
    """Test /ask with empty question"""
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty"

def test_ask_missing_question():
    """Test /ask with missing question field"""
    response = client.post("/ask", json={})
    assert response.status_code == 422 # Validation error

def test_docs_page():
    """Test that docs page is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
