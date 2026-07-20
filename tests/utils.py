# tests/utils.py

async def create_test_user_and_token(client, email: str, role: str):
    """Helper to create a user and login across all test files."""
    # 1. Sign up the user
    await client.post("/auth/signup", json={
        "email": email,
        "password": "testpassword",
        "role": role
    })
    
    # 2. Log them in to get the token
    res = await client.post("/auth/login", json={
        "email": email,
        "password": "testpassword"
    })
    
    return res.json()