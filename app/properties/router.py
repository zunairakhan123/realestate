from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from app.db.session import get_db
from app.core.exceptions import NotFoundError
from app.properties import schemas, service
from app.properties.models import PropertyStatus
from app.core.rate_limit import RateLimiter

# Example: Strict limit of 5 requests per 60 seconds
write_limiter = RateLimiter(max_requests=5, window_seconds=60)

router = APIRouter(prefix="/properties", tags=["Properties"])

@router.post("/", response_model=schemas.PropertyOut, status_code=201,dependencies=[Depends(write_limiter)])
async def create_property(data: schemas.PropertyCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_property(db, data)

# In app/properties/router.py
@router.get("/", response_model=schemas.PropertyList)
async def list_properties(
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    city: Optional[str] = None, status: Optional[PropertyStatus] = None,
    min_price: Optional[float] = None, max_price: Optional[float] = None,
    min_bedrooms: Optional[int] = None, 
    exact_bedrooms: Optional[int] = None,  # Add this line
    db: AsyncSession = Depends(get_db)
):
    total, items = await service.list_properties(db, skip, limit, {
        "city": city, "status": status, "min_price": min_price, 
        "max_price": max_price, "min_bedrooms": min_bedrooms,
        "exact_bedrooms": exact_bedrooms  # Add this line
    })
    return {"total": total, "items": items}

@router.get("/{id}", response_model=schemas.PropertyOut)
async def get_property(id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await service.get_property(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{id}", response_model=schemas.PropertyOut,dependencies=[Depends(write_limiter)])
async def update_property(id: UUID, data: schemas.PropertyUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await service.update_property(db, id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{id}", status_code=204,dependencies=[Depends(write_limiter)])
async def delete_property(id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        await service.delete_property(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))