# from locust import HttpUser, task, between

# # ==========================================
# # Paste your JWT token here
# # ==========================================
# JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3YjRiZTY2Mi02NmFmLTQzY2EtYTc4ZC1kZTlkZjc2OTYwM2YiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3ODQ1NTQ1OTl9.lZKCXUhwoTKkQUVC-MWd4QEpYLRrWUQdyT0YVFQcG1M"

# # ==========================================
# # Replace with a REAL lead UUID
# # ==========================================
# LEAD_ID = "c0b3849b-1281-44c3-93e3-c53b8901ec57"


# class RealtyUser(HttpUser):
#     host = "http://127.0.0.1:8000"

#     # Wait 1–3 seconds between requests
#     wait_time = between(1, 3)

#     def on_start(self):
#         """
#         Runs once when each simulated user starts.
#         Adds the JWT token to every request.
#         """
#         self.client.headers.update({
#             "Authorization": f"Bearer {JWT_TOKEN}",
#             "Content-Type": "application/json",
#             "Accept": "application/json"
#         })

#         print("JWT token added successfully.")

#     @task(3)
#     def view_leads(self):
#         """
#         Busiest READ endpoint.
#         Runs 3x more often than update.
#         """
#         with self.client.get(
#             "/leads/?skip=0&limit=50",
#             name="GET /leads",
#             catch_response=True,
#         ) as response:

#             if response.status_code == 200:
#                 response.success()
#             else:
#                 response.failure(
#                     f"Unexpected Status: {response.status_code}\n{response.text}"
#                 )

#     @task(1)
#     def update_lead_status(self):
#         """
#         Busiest WRITE endpoint.
#         """
#         payload = {
#             "status": "contacted"
#         }

#         with self.client.patch(
#             f"/leads/{LEAD_ID}",
#             json=payload,
#             name="PATCH /leads/{id}",
#             catch_response=True,
#         ) as response:

#             if response.status_code in (200, 204):
#                 response.success()
#             else:
#                 response.failure(
#                     f"Unexpected Status: {response.status_code}\n{response.text}"
#                 )
from locust import HttpUser, task, between

# ==========================================
# Paste your JWT token here
# ==========================================
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3YjRiZTY2Mi02NmFmLTQzY2EtYTc4ZC1kZTlkZjc2OTYwM2YiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3ODQ1NTQ1OTl9.lZKCXUhwoTKkQUVC-MWd4QEpYLRrWUQdyT0YVFQcG1M"

# ==========================================
# Replace with REAL UUIDs from your database
# ==========================================
LEAD_ID = "c0b3849b-1281-44c3-93e3-c53b8901ec57"
PROPERTY_ID = "a07fe184-c732-4cd1-b4b6-ba604db37fd6"  # <-- Update this


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

    # ----------------------------------------------------------------
    # LEADS DOMAIN
    # ----------------------------------------------------------------

    @task(3)
    def view_leads(self):
        """
        Busiest READ endpoint for leads.
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
        Busiest WRITE endpoint for leads.
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

    # ----------------------------------------------------------------
    # PROPERTIES DOMAIN
    # ----------------------------------------------------------------

    @task(3)
    def view_properties(self):
        """
        READ endpoint for properties. 
        Weighted similarly to leads to simulate heavy list-viewing traffic.
        """
        with self.client.get(
            "/properties/?skip=0&limit=50",
            name="GET /properties",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Unexpected Status: {response.status_code}\n{response.text}"
                )

    @task(1)
    def update_property(self):
        """
        WRITE endpoint for properties.
        """
        # Ensure this payload strictly adheres to your PropertyUpdate schema
        payload = {
            "price": 6302.5 
        }

        with self.client.patch(
            f"/properties/{PROPERTY_ID}",
            json=payload,
            name="PATCH /properties/{id}",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 204):
                response.success()
            else:
                response.failure(
                    f"Unexpected Status: {response.status_code}\n{response.text}"
                )