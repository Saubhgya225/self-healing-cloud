from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_prometheus_metrics_endpoint():
    # Make a dummy call to increment request metrics
    client.get("/health/live")
    
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    text = response.text
    assert "http_requests_total" in text
    assert "self_healing_pod_liveness_status" in text
    assert "self_healing_pod_readiness_status" in text
