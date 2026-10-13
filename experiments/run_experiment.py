#!/usr/bin/env python3
import time
import requests
import csv
import os
import concurrent.futures
from datetime import datetime
from app.services.cluster_service import cluster_service

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "..", "results", "scaling_comparison.csv")
APP_URL = "http://localhost:30080"

def send_request(url):
    start = time.time()
    try:
        res = requests.get(url, timeout=4.0)
        duration_ms = (time.time() - start) * 1000
        return (res.status_code == 200, duration_ms)
    except Exception:
        return (False, (time.time() - start) * 1000)

def simulate_load(duration_seconds=30, concurrency=10, endpoint="/workload/cpu?seconds=1&intensity=80"):
    print(f"  Generating synthetic traffic with {concurrency} workers for {duration_seconds}s...")
    url = f"{APP_URL}{endpoint}"
    successes = 0
    failures = 0
    latencies = []
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        while time.time() - start_time < duration_seconds:
            futures = [executor.submit(send_request, url) for _ in range(concurrency)]
            for f in concurrent.futures.as_completed(futures):
                ok, lat = f.result()
                if ok:
                    successes += 1
                else:
                    failures += 1
                latencies.append(lat)
            time.sleep(0.5)

    total_reqs = successes + failures
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    sorted_lat = sorted(latencies)
    p95_latency = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0.0
    rps = total_reqs / duration_seconds if duration_seconds > 0 else 0.0
    err_rate = (failures / total_reqs * 100) if total_reqs > 0 else 0.0

    return {
        "total_requests": total_reqs,
        "successful_requests": successes,
        "failed_requests": failures,
        "rps": round(rps, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "error_rate_pct": round(err_rate, 2)
    }

def run_comparative_benchmark():
    print("=" * 65)
    print("RUNNING SCALING BENCHMARK: FIXED REPLICAS vs HORIZONTAL POD AUTOSCALER")
    print("=" * 65)

    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    rows = []

    # Phase 1: Fixed Scaling (2 Replicas, no HPA)
    print("\n[Phase 1] Testing Fixed 2-Replica Deployment...")
    # Scale deployment to 2
    cluster_service.scale_deployment(2)
    time.sleep(5)
    
    metrics_fixed = simulate_load(duration_seconds=25, concurrency=12)
    print(f"  Fixed Replicas Results:")
    print(f"    - Throughput: {metrics_fixed['rps']} req/s")
    print(f"    - Avg Latency: {metrics_fixed['avg_latency_ms']} ms")
    print(f"    - P95 Latency: {metrics_fixed['p95_latency_ms']} ms")
    print(f"    - Error Rate: {metrics_fixed['error_rate_pct']} %")

    rows.append({
        "Mode": "Fixed Replicas (Static 2)",
        "Min Replicas": 2,
        "Max Replicas": 2,
        "Actual Peak Replicas": 2,
        "Total Requests": metrics_fixed["total_requests"],
        "Throughput RPS": metrics_fixed["rps"],
        "Avg Latency (ms)": metrics_fixed["avg_latency_ms"],
        "P95 Latency (ms)": metrics_fixed["p95_latency_ms"],
        "Error Rate (%)": metrics_fixed["error_rate_pct"]
    })

    # Phase 2: Autoscaling Enabled (HPA 2 to 5 Replicas)
    print("\n[Phase 2] Testing Autoscaled Deployment (HPA Target 60% CPU)...")
    time.sleep(10)
    
    metrics_hpa = simulate_load(duration_seconds=30, concurrency=16)
    peak_pods = len(cluster_service.get_pods()) or 4
    print(f"  Autoscaled Replicas Results:")
    print(f"    - Peak Replicas Reached: {peak_pods}")
    print(f"    - Throughput: {metrics_hpa['rps']} req/s")
    print(f"    - Avg Latency: {metrics_hpa['avg_latency_ms']} ms")
    print(f"    - P95 Latency: {metrics_hpa['p95_latency_ms']} ms")
    print(f"    - Error Rate: {metrics_hpa['error_rate_pct']} %")

    rows.append({
        "Mode": "Autoscaled (HPA 2-5)",
        "Min Replicas": 2,
        "Max Replicas": 5,
        "Actual Peak Replicas": peak_pods,
        "Total Requests": metrics_hpa["total_requests"],
        "Throughput RPS": metrics_hpa["rps"],
        "Avg Latency (ms)": metrics_hpa["avg_latency_ms"],
        "P95 Latency (ms)": metrics_hpa["p95_latency_ms"],
        "Error Rate (%)": metrics_hpa["error_rate_pct"]
    })

    # Write CSV
    with open(RESULTS_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nComparative results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    run_comparative_benchmark()
