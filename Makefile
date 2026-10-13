.PHONY: help build deploy test verify run-benchmarks clean

help:
	@echo "Self-Healing Cloud Platform Makefile commands:"
	@echo "  make build          - Build Docker image into Minikube"
	@echo "  make deploy         - Deploy manifests to Kubernetes"
	@echo "  make test           - Run pytest unit tests"
	@echo "  make verify         - Verify Kubernetes cluster state"
	@echo "  make run-benchmarks - Run failure and autoscaling experiments"
	@echo "  make clean          - Delete Kubernetes namespace"

build:
	bash scripts/setup.sh

deploy:
	bash scripts/deploy.sh

test:
	PYTHONPATH=. pytest -v tests/unit/

verify:
	bash scripts/verify.sh

run-benchmarks:
	PYTHONPATH=. python3 experiments/failure_test.py
	PYTHONPATH=. python3 experiments/run_experiment.py
	PYTHONPATH=. python3 experiments/analyze_results.py

clean:
	bash scripts/cleanup.sh
