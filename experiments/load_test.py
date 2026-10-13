import random
from locust import HttpUser, task, between

class CloudAppUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(5)
    def index_page(self):
        """Simulates normal traffic to root and dashboard."""
        self.client.get("/")

    @task(3)
    def health_check(self):
        """Simulates monitoring probe checks."""
        self.client.get("/health/status")

    @task(2)
    def cpu_intensive_request(self):
        """Simulates CPU load to drive HPA scaling."""
        duration = random.randint(1, 3)
        self.client.get(f"/workload/cpu?seconds={duration}&intensity=70")

    @task(1)
    def latency_simulation(self):
        """Simulates occasional downstream latency."""
        self.client.get("/workload/delay?seconds=0.5")
