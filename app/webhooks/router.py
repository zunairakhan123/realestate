import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException, Header

router = APIRouter()
WEBHOOK_SECRET = "zunaira"

@router.post("/webhooks/inbound")
async def receive_webhook(
    request: Request,
    x_signature: str = Header(None)
):
    if not x_signature:
        raise HTTPException(status_code=401, detail="Missing signature")

    # Validate Signature
    body = await request.body()
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(x_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    # Process the lead creation/update here
    print(f"[*] Valid webhook received: {payload}")
    return {"status": "success"}
