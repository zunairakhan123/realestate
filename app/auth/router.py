import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.auth import schemas, models
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import UserAlreadyExistsError, AuthenticationError

# Must match auth.py settings
SECRET_KEY = "zunaira" 
ALGORITHM = "HS256"

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=schemas.TokenOut, status_code=201)
async def signup(data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Check if user exists
    existing = await db.scalar(select(models.User).where(models.User.email == data.email))
    if existing:
        raise UserAlreadyExistsError(data.email)

    # 2. Hash password and save
    new_user = models.User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 3. Generate Token automatically on signup
    return generate_jwt(new_user)


@router.post("/login", response_model=schemas.TokenOut)
async def login(data: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    # 1. Fetch user by email
    user = await db.scalar(select(models.User).where(models.User.email == data.email))
    
    # 2. Verify existence and password
    if not user or not verify_password(data.password, user.hashed_password):
        raise AuthenticationError()

    # 3. Generate Token
    return generate_jwt(user)


def generate_jwt(user: models.User) -> schemas.TokenOut:
    """Helper function to create the standard token payload"""
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return schemas.TokenOut(
        access_token=token, 
        user_id=str(user.id),
        role=user.role
    )