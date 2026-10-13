from fastapi.testclient import TestClient
from app.main import app
from app.routes.health import set_liveness, set_readiness, reset_health

client = TestClient(app)

def test_liveness_healthy():
    reset_health()
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"

def test_readiness_healthy():
    reset_health()
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"

def test_liveness_failure_injection():
    set_liveness(False, reason="Simulated Kubelet test")
    response = client.get("/health/live")
    assert response.status_code == 500
    data = response.json()
    assert data["status"] == "dead"
    reset_health()

def test_readiness_failure_injection():
    set_readiness(False, reason="Simulated Traffic Isolation test")
    response = client.get("/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unready"
    reset_health()

def test_health_status():
    reset_health()
    response = client.get("/health/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["liveness_healthy"] is True
    assert data["readiness_healthy"] is True
