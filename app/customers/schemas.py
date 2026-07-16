from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


# Common customer fields shared across multiple schemas.
class CustomerBase(BaseModel):
    name: str

    # Validate that the email is in a valid format.
    email: EmailStr

    # Phone number is optional.
    phone: Optional[str] = None


# Schema used when creating a new customer.
# Inherits all required fields from CustomerBase.
class CustomerCreate(CustomerBase):
    pass


# Schema used for partial customer updates.
# All fields are optional so clients can update only the values they need.
class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


# Schema returned in API responses.
class CustomerOut(CustomerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    # Allow Pydantic to create this schema directly from SQLAlchemy ORM objects.
    model_config = ConfigDict(from_attributes=True)


# Paginated response schema.
# Returns the total number of matching customers and the current page of results.
class CustomerList(BaseModel):
    total: int
    items: list[CustomerOut]