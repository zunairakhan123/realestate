from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.leads.models import LeadStatus
from app.customers.schemas import CustomerOut
from app.properties.schemas import PropertyOut

class LeadBase(BaseModel):
    customer_id: Optional[UUID] = None  # <-- Make optional so the backend can set it automatically    
    property_id: UUID
    agent_id: Optional[UUID] = None
    status: LeadStatus = LeadStatus.new
    notes: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    agent_id: Optional[UUID] = None
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None

class LeadOut(LeadBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LeadDetailOut(LeadOut):
    customer: CustomerOut
    property: PropertyOut

class LeadList(BaseModel):
    total: int
    items: list[LeadOut]