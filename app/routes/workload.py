import time
import math
import asyncio
from fastapi import APIRouter, Response, HTTPException, status
from app.config import settings
from app.metrics import WORKLOAD_ACTIVE_TASKS

router = APIRouter(prefix="/workload", tags=["Workload & Stress Testing"])

@router.get("/cpu", summary="Simulate CPU-intensive computation")
async def simulate_cpu(seconds: int = 5, intensity: int = 80):
    """
    Simulates high CPU load to trigger the Horizontal Pod Autoscaler (HPA).
    intensity: Percentage of busy-cycle vs rest (1 - 100).
    """
    intensity = max(10, min(100, intensity))
    seconds = max(1, min(60, seconds))
    
    WORKLOAD_ACTIVE_TASKS.labels(workload_type="cpu", pod_name=settings.POD_NAME).inc()
    start_time = time.time()
    end_time = start_time + seconds

    busy_time = 0.05 * (intensity / 100.0)
    sleep_time = 0.05 * (1.0 - (intensity / 100.0))

    try:
        while time.time() < end_time:
            # Busy work
            cycle_end = time.time() + busy_time
            while time.time() < cycle_end:
                _ = math.sqrt(1234567.89) * math.sin(9876.54)
            if sleep_time > 0.001:
                await asyncio.sleep(sleep_time)
    finally:
        WORKLOAD_ACTIVE_TASKS.labels(workload_type="cpu", pod_name=settings.POD_NAME).dec()

    return {
        "status": "success",
        "workload": "cpu",
        "duration_seconds": seconds,
        "intensity_percent": intensity,
        "pod_name": settings.POD_NAME
    }

@router.get("/memory", summary="Simulate temporary memory consumption")
async def simulate_memory(megabytes: int = 50, duration_seconds: int = 10):
    """
    Allocates memory to test memory limits and monitoring spikes.
    Automatically frees allocated buffer after duration_seconds.
    """
    megabytes = max(5, min(300, megabytes))
    duration_seconds = max(1, min(60, duration_seconds))
    
    WORKLOAD_ACTIVE_TASKS.labels(workload_type="memory", pod_name=settings.POD_NAME).inc()
    try:
        # Allocate bytes (1 MB = 1024 * 1024 bytes)
        buffer = bytearray(megabytes * 1024 * 1024)
        for i in range(0, len(buffer), 4096):
            buffer[i] = 1  # Force resident set memory allocation
        await asyncio.sleep(duration_seconds)
        del buffer
    finally:
        WORKLOAD_ACTIVE_TASKS.labels(workload_type="memory", pod_name=settings.POD_NAME).dec()

    return {
        "status": "success",
        "workload": "memory",
        "allocated_mb": megabytes,
        "held_for_seconds": duration_seconds,
        "pod_name": settings.POD_NAME
    }

@router.get("/delay", summary="Simulate request latency")
async def simulate_delay(seconds: float = 1.0):
    """
    Simulates I/O or downstream latency to test P95 / P99 latency monitoring.
    """
    delay = max(0.1, min(15.0, seconds))
    await asyncio.sleep(delay)
    return {
        "status": "success",
        "latency_seconds": delay,
        "pod_name": settings.POD_NAME
    }

@router.get("/error", summary="Simulate HTTP 500 error")
def simulate_error(code: int = 500):
    """
    Returns an error status code to test Prometheus error rate alerts.
    """
    raise HTTPException(
        status_code=code,
        detail=f"Simulated fault injection error {code} on {settings.POD_NAME}"
    )
