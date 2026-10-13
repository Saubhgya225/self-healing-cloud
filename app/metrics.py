from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# HTTP Request Metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP Requests handled by the application",
    ["method", "endpoint", "http_status", "pod_name"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP Request Latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Number of currently active requests being processed",
    ["pod_name"]
)

# Self-Healing & Health Metrics
POD_LIVENESS_STATUS = Gauge(
    "self_healing_pod_liveness_status",
    "Current liveness status of this pod (1 = healthy, 0 = failing)",
    ["pod_name"]
)

POD_READINESS_STATUS = Gauge(
    "self_healing_pod_readiness_status",
    "Current readiness status of this pod (1 = ready, 0 = unready)",
    ["pod_name"]
)

CHAOS_FAULTS_TOTAL = Counter(
    "self_healing_chaos_faults_injected_total",
    "Total number of chaos failure experiments triggered",
    ["fault_type", "pod_name"]
)

WORKLOAD_ACTIVE_TASKS = Gauge(
    "self_healing_active_workload_tasks",
    "Number of synthetic CPU/Memory stress tasks currently executing",
    ["workload_type", "pod_name"]
)

# Helper function to get raw Prometheus output
def get_prometheus_metrics():
    return generate_latest(), CONTENT_TYPE_LATEST
