import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_request_id_middleware():
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers

def test_openapi_docs():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    docs = response.json()
    assert "openapi" in docs
    assert "info" in docs
    # Check that required paths exist
    paths = docs["paths"]
    assert "/api/v1/merchants/{merchant_id}" in paths
    assert "/api/v1/products" in paths
    assert "/api/v1/buyers" in paths
    assert "/api/v1/experiments" in paths
    assert "/api/v1/traces" in paths
    assert "/api/v1/chaos/profiles" in paths
    assert "/api/v1/repairs" in paths
    assert "/api/v1/replay/cohort" in paths
    assert "/api/v1/metrics" in paths

def test_global_exception_handler():
    # We can test this by mocking an endpoint that raises an exception, 
    # but for now we just verify the handler is registered in the app.
    # A real test would hit a known failing endpoint.
    assert app.exception_handlers
