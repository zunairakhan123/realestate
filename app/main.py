import time
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Routers
from app.auth.router import router as auth_router
from app.customers.router import router as customers_router
from app.properties.router import router as properties_router
from app.leads.router import router as leads_router

# Core & Middleware
from app.core.middleware import RequestLoggingMiddleware
from app.core.events import event_bus
from app.notifications.listeners import handle_terminal_lead

from app.webhooks.router import router as webhook_router  # 1. Import the router

# Exceptions
from app.core.exceptions import (
    PermissionDeniedError,
    AuthenticationError,
    RateLimitExceededError,
    NotFoundError,
    ConflictError
)
from fastapi import WebSocket, WebSocketDisconnect
from app.core.websockets import manager
from app.db.session import get_db  # Updated import path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Depends, HTTPException

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Subscribe the listener to the event on startup
    event_bus.subscribe("lead_terminal_status", handle_terminal_lead)
    yield


# Initialize App
app = FastAPI(title="Realty Service API", lifespan=lifespan)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok"}

@app.get("/ready", tags=["System"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database not ready")

@app.websocket("/ws/leads/{lead_id}")
async def websocket_lead_endpoint(websocket: WebSocket, lead_id: str):
    await manager.connect(websocket, lead_id)
    try:
        while True:
            # Keep the connection open waiting for server pushes
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, lead_id)


# Add Middleware
app.add_middleware(RequestLoggingMiddleware)


# --- Global Exception Handlers ---

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": str(exc),
                "request_id": request.headers.get("X-Request-ID", "unknown")
            }
        }
    )

@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(
        status_code=409,
        content={
            "error": {
                "code": "CONFLICT",
                "message": str(exc),
                "request_id": request.headers.get("X-Request-ID", "unknown")
            }
        }
    )

@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": "FORBIDDEN",
                "message": str(exc),
                "request_id": request.headers.get("X-Request-ID", "unknown")
            }
        }
    )

@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "code": "UNAUTHORIZED",
                "message": str(exc),
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
                "message": str(exc),
                "request_id": request.headers.get("X-Request-ID", "unknown")
            }
        }
    )


# --- Register Routers ---
app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(properties_router)
app.include_router(leads_router)
app.include_router(webhook_router)   #auto-generated Swagger UI (/docs) will group all webhook-related endpoints under a single, easy-to-read section.

# --- Async Proof Endpoints ---

# @app.get("/test-bad-async", tags=["Async Proof"])
# async def bad_async_endpoint():
#     """
#     INCORRECT: A synchronous blocking call inside an async def.
#     This freezes the single-threaded event loop. No other requests can be processed.
#     """
#     time.sleep(1) # Simulating a 1-second blocking task
#     return {"status": "done", "type": "bad"}


# @app.get("/test-good-async", tags=["Async Proof"])
# async def good_async_endpoint():
#     """
#     CORRECT: Yields control back to the event loop.
#     While waiting for this 1-second task to finish, the server handles other requests.
#     """
#     await asyncio.sleep(1) # Simulating a 1-second async I/O task
#     return {"status": "done", "type": "good"}