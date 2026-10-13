#!/usr/bin/env bash
TARGET_URL=${1:-"http://localhost:8000"}
SCENARIO=${2:-"liveness"}

echo "Simulating failure scenario: $SCENARIO against $TARGET_URL"

case "$SCENARIO" in
  liveness)
    echo "Failing liveness probe for 30 seconds..."
    curl -X POST "$TARGET_URL/api/chaos/trigger" \
      -H "Content-Type: application/json" \
      -d '{"fault_type": "liveness", "duration_seconds": 30}'
    ;;
  readiness)
    echo "Failing readiness probe for 30 seconds..."
    curl -X POST "$TARGET_URL/api/chaos/trigger" \
      -H "Content-Type: application/json" \
      -d '{"fault_type": "readiness", "duration_seconds": 30}'
    ;;
  cpu)
    echo "Generating CPU spike (intensity 90%, 15s)..."
    curl "$TARGET_URL/workload/cpu?seconds=15&intensity=90"
    ;;
  reset)
    echo "Resetting all faults..."
    curl -X POST "$TARGET_URL/api/chaos/reset"
    ;;
  *)
    echo "Usage: ./scripts/simulate_chaos.sh [URL] [liveness|readiness|cpu|reset]"
    exit 1
    ;;
esac
echo ""
