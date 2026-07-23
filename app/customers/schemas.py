from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.core.enums import PaymentMethod

# Common customer fields shared across multiple schemas.
class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    payment: PaymentMethod
    notification_preferences: Optional[str] = "email"

# Schema used when creating a new customer internally.
class CustomerCreate(CustomerBase):
    pass

# Schema specifically for public frontend customer registration (includes password for User auth model creation)
class CustomerRegisterSchema(CustomerBase):
    password: str

# Schema used for partial customer updates.
class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    payment: Optional[PaymentMethod] = None
    notification_preferences: Optional[str] = None

# Schema returned in API responses.
class CustomerOut(CustomerBase):
    id: UUID
    user_id: UUID  # <-- CHANGED FROM int TO UUID TO MATCH DATABASE MODEL
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Paginated response schema.
class CustomerList(BaseModel):
    total: int
    items: list[CustomerOut]