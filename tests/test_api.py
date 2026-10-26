from fastapi.testclient import TestClient
from backend.api.server import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["api"] == "operational"

def test_telemetry():
    response = client.get("/api/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "unique_civilians" in data["metrics"]

def test_sitrep_generation():
    response = client.post("/api/sitrep/generate")
    assert response.status_code == 200
    assert "report" in response.json()
    assert "SITREP" in response.json()["report"]