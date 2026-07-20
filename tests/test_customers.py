# tests/test_customers.py
import pytest
from tests.utils import create_test_user_and_token

pytestmark = pytest.mark.asyncio

async def test_delete_customer_with_leads_fails(client):
    auth = await create_test_user_and_token(client, "admin99@test.com", "admin")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    # 1. Create Customer
    cust_res = await client.post("/customers/", json={"name": "John", "email": "j@t.com", "phone": "1"}, headers=headers)
    cust_id = cust_res.json()["id"]

    # 2. Create Property
    prop_res = await client.post("/properties/", json={"address": "456", "city": "City", "price": 100, "bedrooms": 1}, headers=headers)
    prop_id = prop_res.json()["id"]

    # 3. Create Lead attached to customer
    await client.post("/leads/", json={
        "customer_id": cust_id,
        "property_id": prop_id,
        "agent_id": auth["user_id"],
        "status": "new"
    }, headers=headers)

    # 4. Attempt to delete
    delete_res = await client.delete(f"/customers/{cust_id}", headers=headers)

    assert delete_res.status_code == 409

