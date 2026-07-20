# test_ws.py
import asyncio
import websockets
import json
import httpx

# NOTE: Replace these with a real token and lead ID from database
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiNDFlODY3My1iMDE1LTRlNDUtODM0My0wMGJkNTQ2Yjk0YjMiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3ODQ0ODI2Nzl9.vWBWe08KZR0Ixg_syqq9ynMP--icHngSE4uZotktG_A" 
LEAD_ID = "c0b3849b-1281-44c3-93e3-c53b8901ec57"

async def listen_and_trigger():
    uri = f"ws://127.0.0.1:8000/ws/leads/{LEAD_ID}"
    
    async with websockets.connect(uri) as websocket:
        print(f"[*] Connected to WebSocket for Lead: {LEAD_ID}")
        
        # 1. Trigger the REST API update asynchronously while listening
        print("[*] Triggering REST API update...")
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"http://127.0.0.1:8000/leads/{LEAD_ID}",
                json={"status": "contacted"},
                headers={"Authorization": f"Bearer {TOKEN}"}
            )
            
        # 2. Wait for the WebSocket push
        response = await websocket.recv()
        print(f"[+] Received live WebSocket push: {json.loads(response)}")

asyncio.run(listen_and_trigger())