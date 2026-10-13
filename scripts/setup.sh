#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  Self-Healing Cloud Platform: Environment Setup & Build"
echo "=========================================================="

echo "[1/4] Verifying prerequisite tools..."
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not found. Please start Docker."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required but not found in PATH."; exit 1; }
command -v minikube >/dev/null 2>&1 || { echo "minikube is required but not found in PATH."; exit 1; }

echo "[2/4] Verifying Minikube status..."
minikube status >/dev/null 2>&1 || {
    echo "Minikube is not running. Starting Minikube..."
    minikube start --driver=docker
}

echo "[3/4] Enabling Minikube metrics-server addon..."
minikube addons enable metrics-server

echo "[4/4] Building container image inside Minikube..."
# Build image directly into Minikube's Docker daemon
eval $(minikube docker-env)
docker build -t self-healing-app:v1.0.0 -f docker/Dockerfile .

echo "=========================================================="
echo "Setup Complete! Run ./scripts/deploy.sh to deploy platform."
echo "=========================================================="
