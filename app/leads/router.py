from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.leads import schemas, service
from app.leads.models import LeadStatus
from app.core.auth import verify_lead_access, get_current_user
from app.core.rate_limit import RateLimiter
from app.auth.models import User
from app.core.exceptions import BusinessRuleViolation

write_limiter = RateLimiter(max_requests=5, window_seconds=60)

router = APIRouter(prefix="/leads", tags=["Leads"])

@router.post("/", response_model=schemas.LeadOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(write_limiter)])
async def create_lead(
    payload: schemas.LeadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Customer expresses interest in a property via frontend button.
    Automatically provisions a new Lead with status = NEW.
    """
    user_id = current_user.id 
    
    # Pass user_id to correctly resolve the customer profile inside the service layer
    lead = await service.create_lead_from_customer(db, user_id=user_id, payload=payload)
    return lead

# @router.get("/", response_model=schemas.LeadList)
# async def list_leads(
#     skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
#     status: Optional[LeadStatus] = None, agent_id: Optional[str] = None,
#     customer_id: Optional[UUID] = None, property_id: Optional[UUID] = None,
#     created_after: Optional[datetime] = None,
#     is_closed: Optional[bool] = None, 
#     db: AsyncSession = Depends(get_db)
# ):
#     total, items = await service.list_leads(db, skip, limit, {
#         "status": status, "agent_id": agent_id, "customer_id": customer_id, 
#         "property_id": property_id, "created_after": created_after,
#         "is_closed": is_closed 
#     })
#     return {"total": total, "items": items}

@router.get("/", response_model=schemas.LeadList)
async def list_leads(
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    status: Optional[LeadStatus] = None, agent_id: Optional[UUID] = None,
    customer_id: Optional[UUID] = None, property_id: Optional[UUID] = None,
    created_after: Optional[datetime] = None,
    is_closed: Optional[bool] = None, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Pass current_user down to the service layer to handle RBAC filtering cleanly
    total, items = await service.list_leads(
        db, skip, limit, 
        {
            "status": status, "agent_id": agent_id, "customer_id": customer_id, 
            "property_id": property_id, "created_after": created_after,
            "is_closed": is_closed
        },
        current_user=current_user
    )
    return {"total": total, "items": items}

@router.get("/{id}", response_model=schemas.LeadDetailOut, dependencies=[Depends(verify_lead_access)])
async def get_lead(id: UUID, db: AsyncSession = Depends(get_db)):
    return await service.get_lead_detail(db, id)

@router.patch("/{id}", response_model=schemas.LeadOut, dependencies=[Depends(verify_lead_access), Depends(write_limiter)])
async def update_lead(id: UUID, data: schemas.LeadUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await service.update_lead(db, id, data)
    except BusinessRuleViolation as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{id}", status_code=204, dependencies=[Depends(verify_lead_access), Depends(write_limiter)])
async def delete_lead(id: UUID, db: AsyncSession = Depends(get_db)):
    await service.delete_lead(db, id)