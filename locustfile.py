# locustfile.py
from locust import HttpUser, task, between
import random

class RealtyAgentUser(HttpUser):
    # Wait 1 to 3 seconds between tasks to simulate human reading time
    wait_time = between(1, 3) 
    
    def on_start(self):
        """This runs once per user when they spawn. We use it to log in."""
        # Create a unique email for this specific simulated user
        self.email = f"agent_{random.randint(1, 99999)}@loadtest.com"
        
        # 1. Sign up
        self.client.post("/auth/signup", json={
            "email": self.email,
            "password": "loadtestpassword",
            "role": "agent"
        })
        
        # 2. Log in to get the JWT
        response = self.client.post("/auth/login", json={
            "email": self.email,
            "password": "loadtestpassword"
        })
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            # 3. Attach the token to all future requests automatically
            self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(3)
    def view_leads_list(self):
        """Busiest Read Endpoint (Weighted 3x more frequent)"""
        self.client.get("/leads/?skip=0&limit=50")

    @task(1)
    def update_lead_status(self):
        """Busiest Write Endpoint"""
        # Using a dummy UUID. It will return a 404, but it still heavily tests 
        # the JWT middleware, request logger, database connection, and query speed.
        dummy_lead_id = "00000000-0000-0000-0000-000000000000"
        self.client.patch(f"/leads/{dummy_lead_id}", json={
            "status": "contacted"
        })
