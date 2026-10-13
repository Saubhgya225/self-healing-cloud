from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_workload_cpu():
    response = client.get("/workload/cpu?seconds=1&intensity=50")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["workload"] == "cpu"

def test_workload_memory():
    response = client.get("/workload/memory?megabytes=5&duration_seconds=1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["workload"] == "memory"

def test_workload_delay():
    response = client.get("/workload/delay?seconds=0.2")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_workload_error():
    response = client.get("/workload/error?code=500")
    assert response.status_code == 500
    data = response.json()
    assert "Simulated fault" in data["detail"]
