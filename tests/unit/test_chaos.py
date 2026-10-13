from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chaos_liveness_toggle():
    res = client.post("/api/chaos/trigger", json={"fault_type": "liveness", "duration_seconds": 5})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "injected"
    assert data["fault_type"] == "liveness"

    # Verify live probe is failing
    live_res = client.get("/health/live")
    assert live_res.status_code == 500

    # Reset
    reset_res = client.post("/api/chaos/reset")
    assert reset_res.status_code == 200

    # Verify restored
    live_res = client.get("/health/live")
    assert live_res.status_code == 200

def test_chaos_readiness_toggle():
    res = client.post("/api/chaos/trigger", json={"fault_type": "readiness", "duration_seconds": 5})
    assert res.status_code == 200

    ready_res = client.get("/health/ready")
    assert ready_res.status_code == 503

    client.post("/api/chaos/reset")
    ready_res = client.get("/health/ready")
    assert ready_res.status_code == 200
