from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from uuid import UUID
from app.auth.models import UserRole
from app.core.enums import PaymentMethod  # Or use str if preferred

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class CustomerRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    payment: PaymentMethod  # Using your payment method enum/str
    address: Optional[str] = None
    password: str

class AgentCreateRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str  # Can remain str since JWT sub claims are strings
    role: UserRole

class UserResponse(BaseModel):
    id: UUID  # Updated from int to UUID to match the User.id migration change
    email: EmailStr
    role: UserRole

    model_config = ConfigDict(from_attributes=True)