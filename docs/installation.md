# Laptop Setup and Installation Guide

This guide describes how to set up the complete Self-Healing Cloud Infrastructure platform on **Windows 10/11 + WSL2 + Ubuntu 24.04** using 100% free and open-source tools (₹0 Budget).

---

## 1. Prerequisites Checklist

| Component | Minimum Specification | Recommended |
|---|---|---|
| **Operating System** | Windows 10/11 64-bit | Windows 11 with WSL2 |
| **Virtualization** | Enabled in BIOS/UEFI | VT-x / AMD-V Enabled |
| **RAM** | 8 GB | 16 GB |
| **Free Storage** | 20 GB SSD | 30+ GB SSD |

---

## 2. Step-by-Step Installation

### Step 1: WSL 2 & Ubuntu 24.04 Setup
Open PowerShell as Administrator:
```powershell
wsl --install -d Ubuntu-24.04
wsl --set-default-version 2
```
Restart your computer if prompted.

### Step 2: Docker Desktop
1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
2. In the installer, select **Use WSL 2 instead of Hyper-V**.
3. Open Docker Desktop Settings &rarr; **Resources** &rarr; **WSL Integration**.
4. Enable integration with **Ubuntu-24.04** and click **Apply & Restart**.
5. Inside Ubuntu terminal, grant user permissions:
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### Step 3: Kubernetes (Minikube & kubectl)
In your Ubuntu terminal:
```bash
# 1. Install kubectl
sudo snap install kubectl --classic

# 2. Install Minikube
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64

# 3. Start Minikube with Docker driver
minikube start --driver=docker

# 4. Enable Metrics Server (Required for HPA)
minikube addons enable metrics-server
```

### Step 4: Helm & Observability Stack (Prometheus + Grafana)
```bash
# 1. Install Helm
sudo snap install helm --classic

# 2. Add Prometheus Community Helm Repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# 3. Install Prometheus Stack into 'monitoring' namespace
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### Step 5: Python Development Environment
```bash
cd ~/self-healing-cloud
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Verification Commands

Run these commands to verify each subsystem:
```bash
# Docker
docker --version
docker run hello-world

# Kubernetes Cluster
minikube status
kubectl get nodes

# Metrics Server (HPA prerequisite)
kubectl top nodes

# Prometheus & Grafana Pods
kubectl get pods -n monitoring
```
