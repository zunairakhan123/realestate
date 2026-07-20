from locust import HttpUser, task, between

# ==========================================
# Paste your JWT token here
# ==========================================
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwZDNhZWZmOS1iOWUyLTQzOWItYWRmNS0wMTFiNDlkOWUxNzQiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3ODQ1MzkzNjB9.sph4Vg2KDLAsnvi_NjQRUQt4ut418A2DjBfo5wHqtXQ"

# ==========================================
# Replace with a REAL lead UUID
# ==========================================
LEAD_ID = "c0b3849b-1281-44c3-93e3-c53b8901ec57"


class RealtyUser(HttpUser):
    host = "http://127.0.0.1:8000"

    # Wait 1–3 seconds between requests
    wait_time = between(1, 3)

    def on_start(self):
        """
        Runs once when each simulated user starts.
        Adds the JWT token to every request.
        """
        self.client.headers.update({
            "Authorization": f"Bearer {JWT_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        print("JWT token added successfully.")

    @task(3)
    def view_leads(self):
        """
        Busiest READ endpoint.
        Runs 3x more often than update.
        """
        with self.client.get(
            "/leads/?skip=0&limit=50",
            name="GET /leads",
            catch_response=True,
        ) as response:

            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Unexpected Status: {response.status_code}\n{response.text}"
                )

    @task(1)
    def update_lead_status(self):
        """
        Busiest WRITE endpoint.
        """
        payload = {
            "status": "contacted"
        }

        with self.client.patch(
            f"/leads/{LEAD_ID}",
            json=payload,
            name="PATCH /leads/{id}",
            catch_response=True,
        ) as response:

            if response.status_code in (200, 204):
                response.success()
            else:
                response.failure(
                    f"Unexpected Status: {response.status_code}\n{response.text}"
                )
