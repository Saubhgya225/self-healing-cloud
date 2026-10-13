#!/usr/bin/env bash
set -e

echo "=== 1. Checking Pods in self-healing-cloud ==="
kubectl get pods -n self-healing-cloud -o wide

echo "=== 2. Checking Deployment Status ==="
kubectl get deployment -n self-healing-cloud

echo "=== 3. Checking Services ==="
kubectl get svc -n self-healing-cloud

echo "=== 4. Checking Horizontal Pod Autoscaler ==="
kubectl get hpa -n self-healing-cloud

echo "=== 5. Checking Monitoring Pods ==="
kubectl get pods -n monitoring

echo "=== Verification complete! ==="
