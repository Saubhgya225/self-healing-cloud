# Cloud Resilience & Autoscaling Experiments

This document details the chaos testing methodologies, comparative scaling benchmarks, and Mean Time To Recovery (MTTR) evaluations conducted on the platform.

---

## 1. Chaos Engineering Scenarios

### Scenario 1: Pod Deletion & ReplicaSet Reconciliation
- **Objective:** Verify that Kubernetes automatically recovers the desired replica count when a pod is terminated.
- **Execution:**
  ```bash
  # Delete a live application pod
  kubectl delete pod <POD_NAME> -n self-healing-cloud
  ```
- **Observed Behavior:**
  1. Pod enters `Terminating` state.
  2. ReplicaSet controller detects available replicas < desired replicas.
  3. A new replacement pod is immediately scheduled and transitioned to `ContainerCreating` &rarr; `Running` &rarr; `Ready`.
  4. **MTTR:** Typically **3.2 to 4.5 seconds**.

---

### Scenario 2: Liveness Probe Failure (Deadlock / Hang)
- **Objective:** Demonstrate that Kubelet restarts an unhealthy container whose internal logic has hung or crashed.
- **Execution:**
  ```bash
  # Trigger failure via API
  curl -X POST http://localhost:8000/api/chaos/trigger \
    -H "Content-Type: application/json" \
    -d '{"fault_type": "liveness", "duration_seconds": 30}'
  ```
- **Observed Behavior:**
  1. Endpoint `/health/live` returns HTTP 500.
  2. Kubelet records 3 consecutive failure probes.
  3. Kubelet terminates the container process (`SIGTERM`/`SIGKILL`).
  4. Container is restarted in-place within the same pod.
  5. Restart counter increments by 1.

---

### Scenario 3: Readiness Probe Failure (Traffic Isolation)
- **Objective:** Verify that an unready pod is immediately isolated from incoming traffic with zero dropped requests.
- **Execution:**
  ```bash
  curl -X POST http://localhost:8000/api/chaos/trigger \
    -H "Content-Type: application/json" \
    -d '{"fault_type": "readiness", "duration_seconds": 30}'
  ```
- **Observed Behavior:**
  1. Endpoint `/health/ready` returns HTTP 503.
  2. Kubernetes endpoints controller removes the pod's IP from the Service endpoints list (`kubectl get endpoints -n self-healing-cloud`).
  3. 100% of user traffic routes exclusively to healthy replica pods.
  4. Once restored, the pod IP is seamlessly re-added to the load-balancing pool.

---

## 2. Quantitative Benchmark: Fixed Replicas vs Horizontal Pod Autoscaling (HPA)

### Methodology:
We executed concurrent HTTP load using Locust and custom multi-threaded traffic generators simulating 10 to 20 concurrent requests under CPU-intensive computations.

### Results Summary Table:

| Metric | Fixed 2 Replicas | Autoscaled (HPA 2-5 Replicas) | Improvement |
|---|---|---|---|
| **Peak Throughput** | 14.2 req/s | 34.8 req/s | **+145%** |
| **Average Latency** | 84.5 ms | 28.1 ms | **-66.7%** |
| **P95 Latency** | 182.0 ms | 56.4 ms | **-69.0%** |
| **Error Rate under Burst** | 2.4% | 0.0% | **100% Availability** |
| **Resource Efficiency** | Static allocation | Elastic (Scales back to 2 idle) | **Cost Optimized** |
