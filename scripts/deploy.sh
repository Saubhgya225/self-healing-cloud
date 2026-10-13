#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  Deploying Self-Healing Cloud Platform to Kubernetes"
echo "=========================================================="

echo "[1/7] Creating Namespace..."
kubectl apply -f k8s/namespace.yaml

echo "[2/7] Applying RBAC (ServiceAccount, Roles)..."
kubectl apply -f k8s/rbac.yaml

echo "[3/7] Applying ConfigMaps & Secrets..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

echo "[4/7] Applying ResourceQuota & LimitRanges..."
kubectl apply -f k8s/resource-quota.yaml

echo "[5/7] Deploying Self-Healing Application & Service..."
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

echo "[6/7] Applying Horizontal Pod Autoscaler (HPA)..."
kubectl apply -f k8s/hpa.yaml

echo "[7/7] Applying Prometheus ServiceMonitor..."
kubectl apply -f k8s/servicemonitor.yaml || echo "ServiceMonitor applied (or CRD not available, metrics remain accessible via Service)."

echo "Waiting for application pods to become Ready..."
kubectl rollout status deployment/self-healing-app -n self-healing-cloud --timeout=90s

echo "=========================================================="
echo "Deployment successful!"
echo "Access Dashboard locally via:"
echo "  kubectl port-forward -n self-healing-cloud svc/self-healing-service 8000:8000"
echo "  URL: http://localhost:8000"
echo "=========================================================="
