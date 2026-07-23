from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.properties.models import PropertyStatus
from app.core.enums import PropertyType

class PropertyBase(BaseModel):
    address: str
    city: str
    price: float = Field(gt=0)
    bedrooms: int = 0
    property_type: PropertyType = PropertyType.HOME
    status: PropertyStatus = PropertyStatus.available
    image_url: Optional[str] = None
    agent_id: UUID

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    bedrooms: Optional[int] = None
    property_type: Optional[PropertyType] = None
    status: Optional[PropertyStatus] = None
    image_url: Optional[str] = None
    agent_id: Optional[UUID] = None

class PropertyOut(PropertyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PropertyList(BaseModel):
    total: int
    items: list[PropertyOut]