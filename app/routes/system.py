import os
import sys
import time
import asyncio
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.config import settings
from app.metrics import CHAOS_FAULTS_TOTAL
from app.models.schemas import (
    ChaosTriggerRequest,
    ChaosStatusResponse,
    ClusterStatusResponse,
    ExperimentRecord
)
from app.routes.health import set_liveness, set_readiness, reset_health
from app.services.cluster_service import cluster_service
from app.services.monitoring_service import monitoring_service
from app.services.experiment_service import experiment_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["System & Chaos Control"])

@router.get("/system/info", summary="Pod and Host Diagnostic Information")
def system_info():
    """Returns runtime host, pod, and environment information."""
    import platform
    import psutil
    
    mem = psutil.virtual_memory()
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "pod_name": settings.POD_NAME,
        "pod_namespace": settings.POD_NAMESPACE,
        "pod_ip": settings.POD_IP,
        "node_name": settings.NODE_NAME,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": psutil.cpu_count(logical=True),
        "memory_total_mb": round(mem.total / (1024 * 1024), 2),
        "memory_used_mb": round(mem.used / (1024 * 1024), 2),
        "memory_percent": mem.percent,
        "k8s_connected": cluster_service.is_connected()
    }

@router.get("/system/cluster", response_model=ClusterStatusResponse, summary="Live Kubernetes Cluster State")
def get_cluster_state():
    """Returns active pods, deployment replicas, HPA metrics, and recent events."""
    return cluster_service.get_cluster_status()

@router.get("/system/metrics", summary="Live Metrics Summary from Prometheus")
async def get_metrics_summary():
    """Queries Prometheus to retrieve current RPS, error rate, p95 latency, and CPU usage."""
    return await monitoring_service.get_metrics_summary()

@router.post("/chaos/trigger", response_model=ChaosStatusResponse, summary="Trigger a Failure / Chaos Injection")
async def trigger_chaos(request: ChaosTriggerRequest, background_tasks: BackgroundTasks):
    """
    Simulates various cloud infrastructure failures:
    - liveness: Fails /health/live probe (triggers Kubelet restart)
    - readiness: Fails /health/ready probe (removes pod from service endpoints)
    - crash: Kills the python container process immediately (os._exit)
    - delete-pod: Deletes this pod via the Kubernetes API
    """
    fault = request.fault_type.lower()
    CHAOS_FAULTS_TOTAL.labels(fault_type=fault, pod_name=settings.POD_NAME).inc()
    
    if fault == "liveness":
        set_liveness(False, reason="Injected liveness fault via Chaos API")
        if request.duration_seconds and request.duration_seconds > 0:
            import threading
            timer = threading.Timer(request.duration_seconds, lambda: set_liveness(True))
            timer.daemon = True
            timer.start()
        return ChaosStatusResponse(
            status="injected",
            fault_type="liveness",
            pod_name=settings.POD_NAME,
            message="Liveness check is now FAILING (HTTP 500). Kubelet will detect and restart.",
            auto_recover_in_seconds=request.duration_seconds
        )

    elif fault == "readiness":
        set_readiness(False, reason="Injected readiness fault via Chaos API")
        if request.duration_seconds and request.duration_seconds > 0:
            import threading
            timer = threading.Timer(request.duration_seconds, lambda: set_readiness(True))
            timer.daemon = True
            timer.start()
        return ChaosStatusResponse(
            status="injected",
            fault_type="readiness",
            pod_name=settings.POD_NAME,
            message="Readiness check is now FAILING (HTTP 503). Service will stop routing traffic here.",
            auto_recover_in_seconds=request.duration_seconds
        )

    elif fault == "delete-pod":
        # Delete pod using Kubernetes API
        success = cluster_service.delete_pod(settings.POD_NAME)
        if success:
            return ChaosStatusResponse(
                status="injected",
                fault_type="delete-pod",
                pod_name=settings.POD_NAME,
                message=f"Pod {settings.POD_NAME} deleted via Kubernetes API. Deployment controller reconciling."
            )
        else:
            # Fallback if in-cluster RBAC does not permit: exit process
            def exit_soon():
                time.sleep(0.5)
                os._exit(1)
            background_tasks.add_task(exit_soon)
            return ChaosStatusResponse(
                status="injected",
                fault_type="crash",
                pod_name=settings.POD_NAME,
                message="Pod self-terminating to simulate crash and trigger Kubernetes recovery."
            )

    elif fault == "crash":
        def force_crash():
            time.sleep(0.5)
            os._exit(1)
        background_tasks.add_task(force_crash)
        return ChaosStatusResponse(
            status="injected",
            fault_type="crash",
            pod_name=settings.POD_NAME,
            message="Process crashing in 500ms (SIGKILL simulation). Container runtime will restart it."
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported fault type: {fault}")

@router.post("/chaos/reset", summary="Reset All Injected Faults")
def reset_chaos():
    """Restores all health checks to healthy state."""
    reset_health()
    return {
        "status": "reset",
        "pod_name": settings.POD_NAME,
        "message": "All faults cleared. Pod is fully healthy and ready."
    }

@router.get("/experiments", response_model=List[ExperimentRecord], summary="List Recorded Experiments")
def list_experiments():
    """Returns history of all automated self-healing and scaling experiments."""
    return experiment_service.list_experiments()

@router.post("/experiments/run-self-healing-test", summary="Run Automated Pod Recovery Experiment")
async def run_self_healing_test(background_tasks: BackgroundTasks):
    """
    Automated self-healing experiment:
    1. Records initial replica count
    2. Deletes an active pod
    3. Measures Mean Time To Recovery (MTTR) until all pods are Ready
    4. Logs experiment record to database & CSV
    """
    async def run_test():
        pods = cluster_service.get_pods()
        initial_replicas = len(pods)
        if initial_replicas == 0:
            logger.warning("No pods found to run self-healing experiment.")
            return

        target_pod = pods[0].name
        start_time = time.time()
        logger.info(f"Starting self-healing test on pod: {target_pod}")

        # Delete the target pod
        cluster_service.delete_pod(target_pod)

        # Poll until replicas are back to initial count and all are ready
        recovered = False
        timeout = 60
        poll_interval = 1.0
        elapsed = 0.0

        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed = time.time() - start_time
            curr_pods = cluster_service.get_pods()
            ready_count = sum(1 for p in curr_pods if p.ready)
            if ready_count >= initial_replicas and not any(p.name == target_pod for p in curr_pods):
                recovered = True
                break

        recovery_time = round(elapsed, 2)
        status = "RECOVERED" if recovered else "TIMEOUT"
        
        experiment_service.record_experiment(
            scenario="Pod Deletion & Controller Self-Healing",
            initial_replicas=initial_replicas,
            final_replicas=len(cluster_service.get_pods()),
            recovery_time_seconds=recovery_time,
            error_count=0 if recovered else 1,
            status=status,
            notes=f"Deleted pod {target_pod}; reconciled replacement pod in {recovery_time}s"
        )
        logger.info(f"Self-healing experiment finished: status={status}, MTTR={recovery_time}s")

    background_tasks.add_task(run_test)
    return {
        "status": "started",
        "message": "Automated self-healing benchmark started in background. Results will be saved."
    }
