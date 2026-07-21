from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.leads import schemas, service
from app.leads.models import LeadStatus
from app.core.auth import verify_lead_access
from app.core.rate_limit import RateLimiter

# Example: Strict limit of 5 requests per 60 seconds
write_limiter = RateLimiter(max_requests=5, window_seconds=60) #had to increase the limit for locust testing, but in production, you might want to set it lower.

router = APIRouter(prefix="/leads", tags=["Leads"])

@router.post("/", response_model=schemas.LeadOut, status_code=201 ,dependencies=[Depends(write_limiter)])
async def create_lead(data: schemas.LeadCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_lead(db, data)



@router.get("/", response_model=schemas.LeadList, dependencies=[Depends(write_limiter)])
async def list_leads(
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    status: Optional[LeadStatus] = None, agent_id: Optional[str] = None,
    customer_id: Optional[UUID] = None, property_id: Optional[UUID] = None,
    created_after: Optional[datetime] = None,
    is_closed: Optional[bool] = None, 
    db: AsyncSession = Depends(get_db)
):
    total, items = await service.list_leads(db, skip, limit, {
        "status": status, "agent_id": agent_id, "customer_id": customer_id, 
        "property_id": property_id, "created_after": created_after,
        "is_closed": is_closed 
    })
    return {"total": total, "items": items}


# Security Gate applied! No try/except block needed.
@router.get("/{id}", response_model=schemas.LeadDetailOut, dependencies=[Depends(verify_lead_access), Depends(write_limiter)])
async def get_lead(id: UUID, db: AsyncSession = Depends(get_db)):
    return await service.get_lead_detail(db, id)


# Security Gate applied! 
@router.patch("/{id}", response_model=schemas.LeadOut, dependencies=[Depends(verify_lead_access), Depends(write_limiter)])
async def update_lead(id: UUID, data: schemas.LeadUpdate, db: AsyncSession = Depends(get_db)):
    return await service.update_lead(db, id, data)


# Security Gate applied! No try/except block needed.
@router.delete("/{id}", status_code=204, dependencies=[Depends(verify_lead_access), Depends(write_limiter)])
async def delete_lead(id: UUID, db: AsyncSession = Depends(get_db)):
    await service.delete_lead(db, id)


