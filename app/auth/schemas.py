from pydantic import BaseModel, EmailStr
from typing import Literal

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Literal["admin", "agent", "customer"]

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str