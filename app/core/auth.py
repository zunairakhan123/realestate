import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt

from app.db.session import get_db
from app.core.exceptions import PermissionDeniedError
from app.auth.models import User, UserRole
from app.leads import service  

import bcrypt
# Fix for passlib compatibility with modern bcrypt versions
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = bcrypt

from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "zunaira")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate string version to prevent 72-byte limit crashes safely
    truncated = plain_password[:72] if len(plain_password) > 72 else plain_password
    return pwd_context.verify(truncated, hashed_password)

def get_password_hash(password: str) -> str:
    truncated = password[:72] if len(password) > 72 else password
    return pwd_context.hash(truncated)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    
    if user is None or not user.is_active:
        raise credentials_exception
    return user

def require_role(allowed_roles: list[UserRole]):
    def role_dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your security role."
            )
        return current_user
    return role_dependency

async def verify_lead_access(
    id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role == UserRole.ADMIN:
        return user

    if request.method == "DELETE":
        raise PermissionDeniedError("Strict Policy: Only administrators can delete leads.")

    lead = await service.get_lead_detail(db, id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")

    if user.role == UserRole.AGENT:
        if lead.agent_id != user.id:
            raise PermissionDeniedError("Agent is not authorized to access this lead.")
        return user

    if user.role == UserRole.CUSTOMER:
        if request.method not in ["GET", "HEAD", "OPTIONS"]:
            raise PermissionDeniedError("Customers have read-only access and cannot modify leads.")
        if lead.customer_id != user.id:
            raise PermissionDeniedError("Customer is not authorized to view this lead.")
        return user

    raise PermissionDeniedError("Invalid role specified.")

async def verify_property_access(
    request: Request,
    user: User = Depends(get_current_user)
):
    if user.role == UserRole.ADMIN:
        return user

    if user.role == UserRole.CUSTOMER:
        if request.method not in ["GET", "HEAD", "OPTIONS"]:
            raise PermissionDeniedError("Customers have read-only access and cannot modify or delete properties.")
        return user

    if user.role == UserRole.AGENT:
        return user

    raise PermissionDeniedError("Invalid role specified.")

from typing import Annotated
CurrentUser = Annotated[User, Depends(get_current_user)]