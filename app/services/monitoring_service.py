import logging
import httpx
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class MonitoringService:
    def __init__(self):
        self.prometheus_url = settings.PROMETHEUS_URL.rstrip('/')

    async def query(self, promql_query: str) -> Optional[Dict[str, Any]]:
        url = f"{self.prometheus_url}/api/v1/query"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url, params={"query": promql_query})
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Prometheus query error ({response.status_code}): {response.text}")
                    return None
        except Exception as e:
            logger.debug(f"Unable to query Prometheus at {url}: {e}")
            return None

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Fetches key application and infrastructure health metrics from Prometheus."""
        results = {
            "rps": 0.0,
            "error_rate": 0.0,
            "p95_latency_ms": 0.0,
            "cpu_usage_cores": 0.0,
            "prometheus_connected": False
        }

        # Check Prometheus connectivity with basic 'up' query
        up_data = await self.query("up")
        if not up_data or up_data.get("status") != "success":
            return results

        results["prometheus_connected"] = True

        # 1. Total Request Rate (RPS) over last 2 minutes
        rps_data = await self.query('sum(rate(http_requests_total[2m]))')
        if rps_data and rps_data.get("data", {}).get("result"):
            try:
                results["rps"] = round(float(rps_data["data"]["result"][0]["value"][1]), 2)
            except (IndexError, ValueError):
                pass

        # 2. Error Rate (% of 5xx responses)
        err_data = await self.query('sum(rate(http_requests_total{http_status=~"5.."}[2m])) / sum(rate(http_requests_total[2m])) * 100')
        if err_data and err_data.get("data", {}).get("result"):
            try:
                val = float(err_data["data"]["result"][0]["value"][1])
                results["error_rate"] = round(val, 2)
            except (IndexError, ValueError):
                pass

        # 3. P95 Request Latency (ms)
        p95_data = await self.query('histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[2m])) by (le)) * 1000')
        if p95_data and p95_data.get("data", {}).get("result"):
            try:
                val = float(p95_data["data"]["result"][0]["value"][1])
                results["p95_latency_ms"] = round(val, 2)
            except (IndexError, ValueError):
                pass

        # 4. CPU usage of application pods in namespace
        cpu_data = await self.query(f'sum(rate(container_cpu_usage_seconds_total{{namespace="{settings.K8S_NAMESPACE}"}}[2m]))')
        if cpu_data and cpu_data.get("data", {}).get("result"):
            try:
                val = float(cpu_data["data"]["result"][0]["value"][1])
                results["cpu_usage_cores"] = round(val, 3)
            except (IndexError, ValueError):
                pass

        return results

monitoring_service = MonitoringService()
