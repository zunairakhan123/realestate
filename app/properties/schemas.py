from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.properties.models import PropertyStatus

class PropertyBase(BaseModel):
    address: str
    city: str
    price: float = Field(gt=0)
    bedrooms: int = 0
    status: PropertyStatus = PropertyStatus.available

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    bedrooms: Optional[int] = None
    status: Optional[PropertyStatus] = None

class PropertyOut(PropertyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PropertyList(BaseModel):
    total: int
    items: list[PropertyOut]