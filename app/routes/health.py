import time
import asyncio
from fastapi import APIRouter, Response, status
from app.config import settings
from app.metrics import POD_LIVENESS_STATUS, POD_READINESS_STATUS
from app.models.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["Health Checks"])

# In-memory fault states for this specific container
_start_time = time.time()
_is_liveness_healthy = True
_is_readiness_healthy = True
_failure_reason = ""

# Initialize metric gauges
POD_LIVENESS_STATUS.labels(pod_name=settings.POD_NAME).set(1)
POD_READINESS_STATUS.labels(pod_name=settings.POD_NAME).set(1)

def set_liveness(healthy: bool, reason: str = ""):
    global _is_liveness_healthy, _failure_reason
    _is_liveness_healthy = healthy
    _failure_reason = reason
    POD_LIVENESS_STATUS.labels(pod_name=settings.POD_NAME).set(1 if healthy else 0)

def set_readiness(healthy: bool, reason: str = ""):
    global _is_readiness_healthy, _failure_reason
    _is_readiness_healthy = healthy
    _failure_reason = reason
    POD_READINESS_STATUS.labels(pod_name=settings.POD_NAME).set(1 if healthy else 0)

def reset_health():
    set_liveness(True)
    set_readiness(True)

@router.get("/live", summary="Kubernetes Liveness Probe")
def liveness_probe(response: Response):
    """
    Evaluates whether the application is alive.
    If unhealthy (HTTP 500), Kubernetes kubelet will restart the container.
    """
    if not _is_liveness_healthy:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            "status": "dead",
            "pod_name": settings.POD_NAME,
            "error": "Liveness check failed",
            "reason": _failure_reason or "Simulated liveness failure"
        }
    return {
        "status": "alive",
        "pod_name": settings.POD_NAME,
        "uptime_seconds": round(time.time() - _start_time, 2)
    }

@router.get("/ready", summary="Kubernetes Readiness Probe")
def readiness_probe(response: Response):
    """
    Evaluates whether the application is ready to accept user traffic.
    If unready (HTTP 503), Kubernetes Service removes this pod from endpoints.
    """
    if not _is_readiness_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unready",
            "pod_name": settings.POD_NAME,
            "error": "Readiness check failed",
            "reason": _failure_reason or "Simulated readiness failure"
        }
    return {
        "status": "ready",
        "pod_name": settings.POD_NAME
    }

@router.get("/status", response_model=HealthResponse, summary="Comprehensive Health Status")
def health_status():
    """
    Returns full diagnostic information about this pod instance.
    """
    overall_status = "healthy"
    if not _is_liveness_healthy:
        overall_status = "unhealthy_liveness"
    elif not _is_readiness_healthy:
        overall_status = "unhealthy_readiness"

    return HealthResponse(
        status=overall_status,
        pod_name=settings.POD_NAME,
        pod_ip=settings.POD_IP,
        node_name=settings.NODE_NAME,
        uptime_seconds=round(time.time() - _start_time, 2),
        liveness_healthy=_is_liveness_healthy,
        readiness_healthy=_is_readiness_healthy,
        message=_failure_reason if (_failure_reason and overall_status != "healthy") else "Pod is functioning normally"
    )
