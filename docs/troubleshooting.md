# Troubleshooting Guide

This guide addresses common errors and operational hurdles encountered in local cloud-native environments.

---

## 1. Docker Permission Denied
**Symptom:**
```text
permission denied while trying to connect to the Docker API at unix:///var/run/docker.sock
```
**Cause:** Your Ubuntu user is not a member of the `docker` user group.  
**Resolution:**
```bash
sudo usermod -aG docker $USER
newgrp docker
docker info
```

---

## 2. HPA Displays `<unknown>/60%` for CPU Utilization
**Symptom:**
```text
NAME                   REFERENCE                      TARGETS         MINPODS   MAXPODS   REPLICAS
self-healing-app-hpa   Deployment/self-healing-app    <unknown>/60%   2         5         2
```
**Cause:**
1. The Kubernetes Metrics Server addon is disabled or still initializing.
2. The application container does not have `resources.requests.cpu` configured.

**Resolution:**
1. Enable the addon in Minikube:
   ```bash
   minikube addons enable metrics-server
   ```
2. Wait 60 seconds and verify metrics collection:
   ```bash
   kubectl top pods -n self-healing-cloud
   ```
3. Ensure `resources.requests.cpu` is specified in `k8s/deployment.yaml`.

---

## 3. Grafana Port-Forwarding Failed
**Symptom:**
```text
unable to forward port because pod is not running. Current status=Pending
```
**Cause:** Prometheus/Grafana pods are still downloading container images or initializing.  
**Resolution:**
Watch pod statuses until all pods show `Running`:
```bash
kubectl get pods -n monitoring -w
```
Then start port-forwarding:
```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```
Retrieve default admin credentials:
```bash
kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d
```

---

## 4. Minikube Localhost Service Tunneling
**Symptom:** Cannot access NodePort service from Windows browser.  
**Cause:** On Linux/Docker driver, Minikube runs inside a container network.  
**Resolution:**
Run `kubectl port-forward`:
```bash
kubectl port-forward -n self-healing-cloud svc/self-healing-service 8000:8000
```
Then access `http://localhost:8000` in your browser.
