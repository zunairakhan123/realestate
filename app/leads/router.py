from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.db.session import get_db
from app.core.exceptions import NotFoundError
from app.leads import schemas, service
from app.leads.models import LeadStatus

router = APIRouter(prefix="/leads", tags=["Leads"])

@router.post("/", response_model=schemas.LeadOut, status_code=201)
async def create_lead(data: schemas.LeadCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_lead(db, data)

# In app/leads/router.py
@router.get("/", response_model=schemas.LeadList)
async def list_leads(
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    status: Optional[LeadStatus] = None, agent_id: Optional[str] = None,
    customer_id: Optional[UUID] = None, property_id: Optional[UUID] = None,
    created_after: Optional[datetime] = None,
    is_closed: Optional[bool] = None, # Add this line
    db: AsyncSession = Depends(get_db)
):
    total, items = await service.list_leads(db, skip, limit, {
        "status": status, "agent_id": agent_id, "customer_id": customer_id, 
        "property_id": property_id, "created_after": created_after,
        "is_closed": is_closed # Add this line
    })
    return {"total": total, "items": items}
@router.get("/{id}", response_model=schemas.LeadDetailOut)
async def get_lead(id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await service.get_lead_detail(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{id}", response_model=schemas.LeadOut)
async def update_lead(id: UUID, data: schemas.LeadUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await service.update_lead(db, id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{id}", status_code=204)
async def delete_lead(id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        await service.delete_lead(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))