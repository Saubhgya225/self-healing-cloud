import os
import time
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS, get_prometheus_metrics
from app.routes.health import router as health_router
from app.routes.workload import router as workload_router
from app.routes.system import router as system_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Automated Self-Healing, Autoscaling and Infrastructure Monitoring Platform",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus HTTP Request Monitoring Middleware
@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    endpoint = request.url.path
    if endpoint == "/metrics" or endpoint.startswith("/static"):
        return await call_next(request)

    method = request.method
    pod_name = settings.POD_NAME
    ACTIVE_REQUESTS.labels(pod_name=pod_name).inc()
    start_time = time.time()

    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.time() - start_time
        ACTIVE_REQUESTS.labels(pod_name=pod_name).dec()
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            http_status=status_code,
            pod_name=pod_name
        ).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

# Include Routers
app.include_router(health_router)
app.include_router(workload_router)
app.include_router(system_router)

# Mount Dashboard Frontend
dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "dashboard", "frontend")
if os.path.exists(dashboard_dir):
    app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

# Mount Results Directory for CSV download
results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(results_dir, exist_ok=True)
app.mount("/results", StaticFiles(directory=results_dir), name="results")

@app.get("/", summary="Root Redirect to Dashboard")
def root_redirect():
    return RedirectResponse(url="/dashboard/index.html")

@app.get("/metrics", summary="Prometheus Scraping Target")
def prometheus_endpoint():
    content, media_type = get_prometheus_metrics()
    return Response(content=content, media_type=media_type)
