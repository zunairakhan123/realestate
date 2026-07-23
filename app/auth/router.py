from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

from app.db.session import get_db
from app.auth import schemas, models
from app.auth.models import User, UserRole
from app.auth.schemas import TokenResponse, UserResponse, AgentCreateRequest, UserCreate
from app.core.auth import verify_password, create_access_token, get_current_user, get_password_hash, require_role, SECRET_KEY, ALGORITHM
from app.core.exceptions import UserAlreadyExistsError, AuthenticationError

router = APIRouter(prefix="/auth", tags=["Authentication"])

def generate_jwt(user: models.User) -> schemas.TokenResponse:
    """Helper function to create the standard token payload with role and subject."""
    payload = {
        "sub": str(user.id),
        "role": user.role.value if hasattr(user.role, "value") else user.role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return schemas.TokenResponse(
        access_token=token, 
        token_type="bearer",
        user_id=str(user.id),
        role=user.role
    )

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Public signup endpoint. 
    SECURITY FIX: Role is hardcoded to CUSTOMER to prevent privilege escalation.
    """
    existing_result = await db.execute(select(User).where(User.email == data.email))
    if existing_result.scalars().first():
        raise UserAlreadyExistsError(data.email)

    new_user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return generate_jwt(new_user)

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Common login endpoint for Customers, Agents, and Admins."""
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        raise AuthenticationError()
    
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "user_id": str(user.id)}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Returns the currently authenticated user based on JWT headers."""
    return current_user

@router.post("/admin/agents", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Admin-only endpoint to securely provision Agent accounts."""
    result = await db.execute(select(User).filter(User.email == payload.email))
    if result.scalars().first():
        raise UserAlreadyExistsError(payload.email)

    new_agent = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.AGENT,
        is_active=True
    )
    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)
    return new_agent