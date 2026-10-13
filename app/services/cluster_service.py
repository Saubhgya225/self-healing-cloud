import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.config import settings
from app.models.schemas import PodInfo, DeploymentInfo, HPAInfo, ClusterStatusResponse

logger = logging.getLogger(__name__)

class ClusterService:
    def __init__(self):
        self._k8s_client = None
        self._core_v1 = None
        self._apps_v1 = None
        self._autoscaling_v2 = None
        self._init_client()

    def _init_client(self):
        try:
            from kubernetes import client, config
            try:
                # Try in-cluster first (when running as pod)
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes configuration.")
            except Exception:
                # Fallback to local kubeconfig (~/.kube/config)
                config.load_kube_config()
                logger.info("Loaded local kubeconfig.")
            
            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.AppsV1Api()
            self._autoscaling_v2 = client.AutoscalingV2Api()
            self._k8s_client = client
        except Exception as e:
            logger.warning(f"Could not initialize Kubernetes client: {e}. Running in standalone mock mode.")

    def is_connected(self) -> bool:
        return self._core_v1 is not None

    def get_pods(self, namespace: Optional[str] = None) -> List[PodInfo]:
        ns = namespace or settings.K8S_NAMESPACE
        if not self.is_connected():
            return []

        try:
            pod_list = self._core_v1.list_namespaced_pod(namespace=ns)
            results = []
            now = datetime.now(timezone.utc)
            for pod in pod_list.items:
                # Check if all containers are ready
                ready = False
                restart_count = 0
                if pod.status and pod.status.container_statuses:
                    ready = all(cs.ready for cs in pod.status.container_statuses)
                    restart_count = sum(cs.restart_count for cs in pod.status.container_statuses)

                age_seconds = 0
                if pod.metadata.creation_timestamp:
                    age_seconds = int((now - pod.metadata.creation_timestamp).total_seconds())

                results.append(PodInfo(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    phase=pod.status.phase or "Unknown",
                    ready=ready,
                    restart_count=restart_count,
                    pod_ip=pod.status.pod_ip,
                    node_name=pod.spec.node_name,
                    age_seconds=max(0, age_seconds)
                ))
            return results
        except Exception as e:
            logger.error(f"Error fetching pods from namespace {ns}: {e}")
            return []

    def get_deployment(self, name: Optional[str] = None, namespace: Optional[str] = None) -> Optional[DeploymentInfo]:
        dep_name = name or settings.K8S_DEPLOYMENT_NAME
        ns = namespace or settings.K8S_NAMESPACE
        if not self.is_connected():
            return None

        try:
            dep = self._apps_v1.read_namespaced_deployment(name=dep_name, namespace=ns)
            status = dep.status
            spec = dep.spec
            return DeploymentInfo(
                name=dep.metadata.name,
                namespace=dep.metadata.namespace,
                desired_replicas=spec.replicas or 0,
                ready_replicas=status.ready_replicas or 0,
                available_replicas=status.available_replicas or 0,
                updated_replicas=status.updated_replicas or 0
            )
        except Exception as e:
            logger.error(f"Error reading deployment {dep_name}: {e}")
            return None

    def get_hpa(self, name: Optional[str] = None, namespace: Optional[str] = None) -> Optional[HPAInfo]:
        hpa_name = name or settings.K8S_HPA_NAME
        ns = namespace or settings.K8S_NAMESPACE
        if not self.is_connected():
            return None

        try:
            hpa = self._autoscaling_v2.read_namespaced_horizontal_pod_autoscaler(name=hpa_name, namespace=ns)
            curr_cpu = None
            target_cpu = None

            if hpa.spec.metrics:
                for m in hpa.spec.metrics:
                    if m.type == "Resource" and m.resource.name == "cpu":
                        target_cpu = m.resource.target.average_utilization

            if hpa.status.current_metrics:
                for m in hpa.status.current_metrics:
                    if m.type == "Resource" and m.resource.name == "cpu":
                        curr_cpu = m.resource.current.average_utilization

            return HPAInfo(
                name=hpa.metadata.name,
                namespace=hpa.metadata.namespace,
                min_replicas=hpa.spec.min_replicas or 1,
                max_replicas=hpa.spec.max_replicas,
                current_replicas=hpa.status.current_replicas or 0,
                desired_replicas=hpa.status.desired_replicas or 0,
                current_cpu_utilization=curr_cpu,
                target_cpu_utilization=target_cpu
            )
        except Exception as e:
            logger.error(f"Error reading HPA {hpa_name}: {e}")
            return None

    def get_events(self, namespace: Optional[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
        ns = namespace or settings.K8S_NAMESPACE
        if not self.is_connected():
            return []

        try:
            event_list = self._core_v1.list_namespaced_event(namespace=ns)
            sorted_events = sorted(
                event_list.items,
                key=lambda x: x.last_timestamp or x.event_time or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )
            events = []
            for ev in sorted_events[:limit]:
                events.append({
                    "reason": ev.reason,
                    "message": ev.message,
                    "type": ev.type,
                    "object": f"{ev.involved_object.kind}/{ev.involved_object.name}" if ev.involved_object else "Unknown",
                    "time": ev.last_timestamp.isoformat() if ev.last_timestamp else ""
                })
            return events
        except Exception as e:
            logger.error(f"Error reading events: {e}")
            return []

    def delete_pod(self, pod_name: str, namespace: Optional[str] = None) -> bool:
        ns = namespace or settings.K8S_NAMESPACE
        if not self.is_connected():
            return False
        try:
            self._core_v1.delete_namespaced_pod(name=pod_name, namespace=ns)
            logger.info(f"Deleted pod {pod_name} in namespace {ns}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete pod {pod_name}: {e}")
            return False

    def scale_deployment(self, replicas: int, name: Optional[str] = None, namespace: Optional[str] = None) -> bool:
        dep_name = name or settings.K8S_DEPLOYMENT_NAME
        ns = namespace or settings.K8S_NAMESPACE
        if not self.is_connected():
            return False
        try:
            self._apps_v1.patch_namespaced_deployment_scale(
                name=dep_name,
                namespace=ns,
                body={"spec": {"replicas": replicas}}
            )
            logger.info(f"Scaled deployment {dep_name} to {replicas} replicas")
            return True
        except Exception as e:
            logger.error(f"Failed to scale deployment {dep_name}: {e}")
            return False

    def get_cluster_status(self) -> ClusterStatusResponse:
        return ClusterStatusResponse(
            deployment=self.get_deployment(),
            hpa=self.get_hpa(),
            pods=self.get_pods(),
            events=self.get_events()
        )

cluster_service = ClusterService()
