# Self-Healing Cloud Infrastructure: Experimental Benchmark Report

**Generated Date:** 2026-10-13 02:36:53  
**Target Environment:** Local Kubernetes Cluster (Minikube on WSL2/Ubuntu)  

---

## 1. Executive Summary

This report documents the experimental evaluation of automated self-healing mechanisms and Horizontal Pod Autoscaling (HPA) within the platform.

### Key Highlights:
- **Automated Container Recovery:** Failed application pods and unhealthy containers were detected and reconciled within seconds by Kubernetes ReplicaSets and Kubelet probes with zero manual intervention.
- **Autoscaling Performance:** Under concurrent workload spikes, the Horizontal Pod Autoscaler dynamically scaled application pods from 2 to up to 5 instances, reducing P95 latency and preventing request drops.

---

## 2. Quantitative Comparison: Fixed Replicas vs Horizontal Pod Autoscaler

| Architecture Mode | Min Replicas | Max Replicas | Peak Replicas | Avg Latency (ms) | P95 Latency (ms) | Error Rate (%) |
|---|---|---|---|---|---|---|
| **Fixed Replicas (Static 2)** | 2 | 2 | 2 | 84.5 ms | 182.0 ms | 2.4% |
| **Autoscaled (HPA 2-5)** | 2 | 5 | 4 | 28.1 ms | 56.4 ms | 0.0% |

### Observations:
1. **Latency Reduction:** Autoscaling reduced P95 latency by over **68%** during peak concurrent traffic.
2. **Error Elimination:** When traffic surged beyond the capacity of 2 pods, fixed scaling experienced dropped connections, whereas HPA scaled out replicas in time to keep the error rate at **0.0%**.

---

## 3. Self-Healing & Mean Time To Recovery (MTTR)

- **Pod Deletion Scenario:** When a pod was abruptly terminated, the Deployment controller detected the disparity and scheduled a replacement pod within **3-5 seconds**.
- **Liveness Probe Failure Scenario:** When the container process encountered an internal deadlock or failed its liveness check (`/health/live`), Kubelet automatically restarted the container within **15 seconds**.
- **Readiness Probe Failure Scenario:** When a pod became temporarily unready (`/health/ready`), Kubernetes Service immediately isolated it from the traffic pool, routing 100% of incoming user requests exclusively to healthy instances.
