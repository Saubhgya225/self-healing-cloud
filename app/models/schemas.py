from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class HealthResponse(BaseModel):
    status: str
    pod_name: str
    pod_ip: str
    node_name: str
    uptime_seconds: float
    liveness_healthy: bool
    readiness_healthy: bool
    message: Optional[str] = None

class ChaosTriggerRequest(BaseModel):
    fault_type: str = Field(..., description="Type of fault: liveness, readiness, crash, cpu, memory")
    duration_seconds: Optional[int] = Field(default=30, description="Auto-recovery duration in seconds, if applicable")
    intensity: Optional[int] = Field(default=50, description="Intensity level (e.g. CPU% or MB memory)")

class ChaosStatusResponse(BaseModel):
    status: str
    fault_type: str
    pod_name: str
    message: str
    auto_recover_in_seconds: Optional[int] = None

class WorkloadRequest(BaseModel):
    seconds: int = 5
    intensity: int = 50

class PodInfo(BaseModel):
    name: str
    namespace: str
    phase: str
    ready: bool
    restart_count: int
    pod_ip: Optional[str] = None
    node_name: Optional[str] = None
    age_seconds: int

class DeploymentInfo(BaseModel):
    name: str
    namespace: str
    desired_replicas: int
    ready_replicas: int
    available_replicas: int
    updated_replicas: int

class HPAInfo(BaseModel):
    name: str
    namespace: str
    min_replicas: int
    max_replicas: int
    current_replicas: int
    desired_replicas: int
    current_cpu_utilization: Optional[int] = None
    target_cpu_utilization: Optional[int] = None

class ClusterStatusResponse(BaseModel):
    deployment: Optional[DeploymentInfo] = None
    hpa: Optional[HPAInfo] = None
    pods: List[PodInfo] = []
    events: List[Dict[str, Any]] = []

class ExperimentRecord(BaseModel):
    experiment_id: str
    scenario: str
    start_time: str
    end_time: Optional[str] = None
    recovery_time_seconds: Optional[float] = None
    initial_replicas: int
    final_replicas: int
    error_count: int
    status: str
    notes: Optional[str] = None
