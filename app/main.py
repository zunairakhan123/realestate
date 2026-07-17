from fastapi import FastAPI
from app.customers.router import router as customers_router
from app.properties.router import router as properties_router
from app.leads.router import router as leads_router
from fastapi import FastAPI
from app.core.middleware import RequestLoggingMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import PermissionDeniedError
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from app.core.exceptions import RateLimitExceededError
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.events import event_bus
from app.notifications.listeners import handle_terminal_lead
import time
import asyncio
from fastapi import APIRouter

# Use FastAPI's modern lifespan manager for startup events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Subscribe the listener to the event
    event_bus.subscribe("lead_terminal_status", handle_terminal_lead)
    yield
    # Teardown logic (if any) would go here

# Attach lifespan to app
app = FastAPI(title="Realty Service API", lifespan=lifespan)
# Add the middleware
app.add_middleware(RequestLoggingMiddleware)

# Add this just for testing your endpoints
@app.get("/generate-token")
def get_test_token(user_id: str, role: str):
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=2) # Expires in 2 hours
    }
    # Must match the secret in auth.py
    token = jwt.encode(payload, "zunaira", algorithm="HS256")
    return {"access_token": token}

@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    # Standard error envelope
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": "FORBIDDEN",
                "message": exc.message,
                "request_id": request.headers.get("X-Request-ID", "unknown")
            }
        }
    )
@app.exception_handler(RateLimitExceededError)
async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "TOO_MANY_REQUESTS",
                "message": exc.message,
                "request_id": request.headers.get("X-Request-ID", "unknown")
            }
        }
    )

app.include_router(customers_router)
app.include_router(properties_router)
app.include_router(leads_router)


@app.get("/test-bad-async")
async def bad_async_endpoint():
    """
    INCORRECT: A synchronous blocking call inside an async def.
    This freezes the single-threaded event loop. No other requests can be processed.
    """
    time.sleep(1) # Simulating a 1-second blocking task
    return {"status": "done", "type": "bad"}


@app.get("/test-good-async")
async def good_async_endpoint():
    """
    CORRECT: Yields control back to the event loop.
    While waiting for this 1-second task to finish, the server handles other requests.
    """
    await asyncio.sleep(1) # Simulating a 1-second async I/O task
    return {"status": "done", "type": "good"}