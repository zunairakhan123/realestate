import pytest
from tests.utils import create_test_user_and_token

pytestmark = pytest.mark.asyncio

async def test_update_sold_property_fails(client):
    auth = await create_test_user_and_token(client, "admin2@test.com", "admin")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    # 1. Create a sold property
    prop_res = await client.post("/properties/", json={
        "address": "123 Sold Lane",
        "city": "Testville",
        "price": 500000,
        "bedrooms": 3,
        "status": "sold" # Marked as sold immediately
    }, headers=headers)
    prop_id = prop_res.json()["id"]

    # 2. Attempt to update its price
    update_res = await client.patch(f"/properties/{prop_id}", json={"price": 450000}, headers=headers)

    # 3. Assert the business rule blocked it
    assert update_res.status_code == 409
    assert "sold" in update_res.json()["error"]["message"].lower()