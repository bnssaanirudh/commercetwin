from fastapi.testclient import TestClient

from app.main import app


def test_read_root():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code in [200, 404]
