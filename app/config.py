import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "self-healing-cloud")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Pod Metadata (Injected by Kubernetes Downward API)
    POD_NAME: str = os.getenv("POD_NAME", "local-standalone-pod")
    POD_NAMESPACE: str = os.getenv("POD_NAMESPACE", "self-healing-cloud")
    POD_IP: str = os.getenv("POD_IP", "127.0.0.1")
    NODE_NAME: str = os.getenv("NODE_NAME", "minikube")
    
    # Prometheus & Cluster URLs
    PROMETHEUS_URL: str = os.getenv(
        "PROMETHEUS_URL", 
        "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090"
    )
    K8S_NAMESPACE: str = os.getenv("K8S_NAMESPACE", "self-healing-cloud")
    K8S_DEPLOYMENT_NAME: str = os.getenv("K8S_DEPLOYMENT_NAME", "self-healing-app")
    K8S_HPA_NAME: str = os.getenv("K8S_HPA_NAME", "self-healing-app-hpa")

settings = Settings()
