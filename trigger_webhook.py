import requests
import hmac
import hashlib
import json

WEBHOOK_URL = "https://defend-flashers-selling-given.trycloudflare.com/webhooks/inbound"
SECRET = "zunaira"
payload = {"lead_email": "external@test.com", "status": "new"}
body = json.dumps(payload).encode()

# Generate the signature
signature = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()

response = requests.post(
    WEBHOOK_URL, 
    data=body, 
    headers={"X-Signature": signature, "Content-Type": "application/json"}
)
print(f"Response: {response.status_code}")