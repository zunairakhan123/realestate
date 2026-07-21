import jwt
from typing import Optional
from uuid import UUID
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.core.exceptions import PermissionDeniedError
from app.leads import service

# 1. JWT Configuration (In production, load SECRET_KEY from .env)
SECRET_KEY = "zunaira"
ALGORITHM = "HS256"

# FastAPI built-in scheme to extract "Authorization: Bearer "
security = HTTPBearer()

class CurrentUser(BaseModel):
    id: str
    role: str

# 2. Extract and Verify the Token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    token = credentials.credentials
    try:
        # Cryptographically verify the token hasn't been tampered with
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        
        if user_id is None or role is None:
            raise PermissionDeniedError("Invalid token payload: missing 'sub' or 'role'.")
            
        return CurrentUser(id=user_id, role=role)
        
    except jwt.ExpiredSignatureError:
        raise PermissionDeniedError("Token has expired.")
    except jwt.PyJWTError:
        raise PermissionDeniedError("Could not validate credentials.")

# 3. Method-Aware Dependency (Stays EXACTLY the same!)
async def verify_lead_access(
    id: UUID,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role == "admin":
        return user

    if request.method == "DELETE":
        raise PermissionDeniedError("Strict Policy: Only administrators can delete leads.")

    lead = await service.get_lead_detail(db, id)

    if user.role == "agent":
        if str(lead.agent_id) != user.id:
            raise PermissionDeniedError("Agent is not authorized to access this lead.")
        return user

    if user.role == "customer":
        if request.method not in ["GET", "HEAD", "OPTIONS"]:
            raise PermissionDeniedError("Customers have read-only access and cannot modify leads.")
        if str(lead.customer_id) != user.id:
            raise PermissionDeniedError("Customer is not authorized to view this lead.")
        return user

    raise PermissionDeniedError("Invalid role specified.")

async def verify_property_access(
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    # Admins can perform any action
    if user.role == "admin":
        return user

    # Restrict customers to read-only methods
    if user.role == "customer":
        if request.method not in ["GET", "HEAD", "OPTIONS"]:
            raise PermissionDeniedError("Customers have read-only access and cannot modify or delete properties.")
        return user

    # Allow agents to modify properties (add specific ownership checks here later if needed)
    if user.role == "agent":
        return user

    raise PermissionDeniedError("Invalid role specified.")