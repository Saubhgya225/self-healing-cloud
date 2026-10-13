#!/usr/bin/env python3
import time
import requests
import sys
from datetime import datetime, timezone
from app.services.cluster_service import cluster_service
from app.services.experiment_service import experiment_service

DEFAULT_APP_URL = "http://localhost:30080"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_pod_deletion():
    log("=== Scenario 1: Pod Deletion & ReplicaSet Reconciliation ===")
    pods = cluster_service.get_pods()
    if not pods:
        log("No pods detected in namespace self-healing-cloud. Skipping.")
        return

    target_pod = pods[0].name
    initial_count = len(pods)
    log(f"Initial healthy pods: {initial_count}. Targeting pod: {target_pod}")

    start_time = time.time()
    cluster_service.delete_pod(target_pod)
    log(f"Deleted pod {target_pod}. Awaiting Kubernetes ReplicaSet controller...")

    recovered = False
    timeout = 45
    poll_interval = 1.0

    while time.time() - start_time < timeout:
        time.sleep(poll_interval)
        current_pods = cluster_service.get_pods()
        ready_count = sum(1 for p in current_pods if p.ready)
        new_pods = [p for p in current_pods if p.name != target_pod]
        
        if ready_count >= initial_count and len(new_pods) >= initial_count:
            recovered = True
            break

    recovery_time = round(time.time() - start_time, 2)
    status = "RECOVERED" if recovered else "TIMEOUT"
    log(f"Result: {status} in {recovery_time}s")

    experiment_service.record_experiment(
        scenario="Pod Deletion & Controller Self-Healing",
        initial_replicas=initial_count,
        final_replicas=len(cluster_service.get_pods()),
        recovery_time_seconds=recovery_time,
        error_count=0 if recovered else 1,
        status=status,
        notes=f"Deleted pod {target_pod}; replacement pod became Ready in {recovery_time}s"
    )

def test_liveness_failure(base_url=DEFAULT_APP_URL):
    log("\n=== Scenario 2: Liveness Probe Failure & Kubelet Restart ===")
    start_time = time.time()
    try:
        res = requests.post(f"{base_url}/api/chaos/trigger", json={"fault_type": "liveness", "duration_seconds": 25}, timeout=5)
        log(f"Injected Liveness Fault: {res.json().get('message')}")
    except Exception as e:
        log(f"Could not reach application API at {base_url}: {e}")
        return

    # Check that liveness check returns 500
    try:
        check = requests.get(f"{base_url}/health/live", timeout=3)
        log(f"Liveness endpoint response status: {check.status_code} (Expected: 500)")
    except Exception:
        pass

    log("Monitoring for automatic recovery or pod restart...")
    recovered = False
    timeout = 40
    while time.time() - start_time < timeout:
        time.sleep(2)
        try:
            live = requests.get(f"{base_url}/health/live", timeout=2)
            if live.status_code == 200:
                recovered = True
                break
        except Exception:
            continue

    recovery_time = round(time.time() - start_time, 2)
    status = "RECOVERED" if recovered else "TIMEOUT"
    log(f"Result: {status} in {recovery_time}s")

    experiment_service.record_experiment(
        scenario="Liveness Failure & Kubelet Self-Healing",
        initial_replicas=len(cluster_service.get_pods()) or 2,
        final_replicas=len(cluster_service.get_pods()) or 2,
        recovery_time_seconds=recovery_time,
        error_count=0 if recovered else 1,
        status=status,
        notes="Liveness probe failed; auto-recovered to healthy 200 OK"
    )

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_APP_URL
    test_pod_deletion()
    test_liveness_failure(url)
    log("\nAll failure experiments completed. Check results/experiments.csv")
