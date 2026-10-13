#!/usr/bin/env bash
echo "Cleaning up self-healing-cloud resources..."
kubectl delete namespace self-healing-cloud --ignore-not-found=true
echo "Cleanup completed."
