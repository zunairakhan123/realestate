from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.db.session import get_db
from app.core.config import get_settings, Settings
from app.core.exceptions import NotFoundError, ConflictError
from app.customers import schemas, service
from app.core.rate_limit import RateLimiter
from app.core.auth import require_role, get_current_user
from app.auth.models import UserRole, User

write_limiter = RateLimiter(max_requests=5, window_seconds=60)

router = APIRouter(prefix="/customers", tags=["Customers"])

# Create a new customer profile + user account via public frontend registration
@router.post("/", response_model=schemas.CustomerOut, status_code=201, dependencies=[Depends(write_limiter)])
async def create_customer(
    data: schemas.CustomerRegisterSchema,  # <-- CHANGED TO ACCEPT PASSWORD
    db: AsyncSession = Depends(get_db)
):
    try:
        return await service.create_customer(db, data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


# Return a paginated list of customers (Restricted to Admins and Agents)
@router.get("/", response_model=schemas.CustomerList)
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    has_active_leads: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.AGENT]))
):
    total, items = await service.list_customers(
        db,
        skip,
        limit,
        {
            "name": name,
            "email": email,
            "phone": phone,
            "created_after": created_after,
            "created_before": created_before,
            "has_active_leads": has_active_leads,
        },
    )

    return {
        "total": total,
        "items": items,
    }


# Retrieve a customer by unique ID
@router.get("/{id}", response_model=schemas.CustomerOut)
async def get_customer(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.AGENT, UserRole.CUSTOMER]))
):
    try:
        return await service.get_customer(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Partially update an existing customer
@router.patch("/{id}", response_model=schemas.CustomerOut, dependencies=[Depends(write_limiter)])
async def update_customer(
    id: UUID,
    data: schemas.CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.AGENT, UserRole.CUSTOMER]))
):
    try:
        return await service.update_customer(db, id, data)
    except (NotFoundError, ConflictError) as e:
        raise HTTPException(
            status_code=404 if isinstance(e, NotFoundError) else 409,
            detail=str(e),
        )


# Delete a customer (Restricted to Admins)
@router.delete("/{id}", status_code=204, dependencies=[Depends(write_limiter)])
async def delete_customer(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    try:
        await service.delete_customer(
            db,
            id,
            settings.enforce_customer_delete_guard,
        )

    except (NotFoundError, ConflictError) as e:
        raise HTTPException(
            status_code=404 if isinstance(e, NotFoundError) else 409,
            detail=str(e),
        )