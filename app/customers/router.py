from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.db.session import get_db
from app.core.config import get_settings, Settings
from app.core.exceptions import NotFoundError, ConflictError
from app.customers import schemas, service

# Routes for customer management.
router = APIRouter(prefix="/customers", tags=["Customers"])


# Create a new customer.
# Returns HTTP 409 if the email already exists.
@router.post("/", response_model=schemas.CustomerOut, status_code=201)
async def create_customer(
    data: schemas.CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await service.create_customer(db, data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


# Return a paginated list of customers with optional search filters.
@router.get("/", response_model=schemas.CustomerList)
async def list_customers(
    # Pagination parameters.
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),

    # Optional filters.
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    has_active_leads: Optional[bool] = None, # Add this line

    # Database session provided by FastAPI dependency injection.
    db: AsyncSession = Depends(get_db)
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


# Retrieve a customer by its unique ID.
@router.get("/{id}", response_model=schemas.CustomerOut)
async def get_customer(
    id: UUID,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await service.get_customer(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Partially update an existing customer.
# Only the fields provided in the request are modified.
@router.patch("/{id}", response_model=schemas.CustomerOut)
async def update_customer(
    id: UUID,
    data: schemas.CustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await service.update_customer(db, id, data)
    except (NotFoundError, ConflictError) as e:
        raise HTTPException(
            status_code=404 if isinstance(e, NotFoundError) else 409,
            detail=str(e),
        )


# Delete a customer.
# Business rules may prevent deletion if the customer has active leads.
@router.delete("/{id}", status_code=204)
async def delete_customer(
    id: UUID,
    db: AsyncSession = Depends(get_db),

    # Load application settings through dependency injection.
    settings: Settings = Depends(get_settings),
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