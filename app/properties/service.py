from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.properties.models import Property
from app.properties.schemas import PropertyCreate, PropertyUpdate
from app.core.exceptions import ConflictError, NotFoundError

async def create_property(db: AsyncSession, data: PropertyCreate) -> Property:
    prop = Property(**data.model_dump())
    db.add(prop)
    await db.commit()
    await db.refresh(prop)
    return prop

async def list_properties(db: AsyncSession, skip: int, limit: int, filters: dict):
    stmt = select(Property)
    if filters.get("city"):
        stmt = stmt.where(Property.city.ilike(f"%{filters['city']}%"))
    if filters.get("status"):
        stmt = stmt.where(Property.status == filters["status"])
    if filters.get("property_type"):
        stmt = stmt.where(Property.property_type == filters["property_type"])
    if filters.get("agent_id"):
        stmt = stmt.where(Property.agent_id == filters["agent_id"])
    if filters.get("min_price"):
        stmt = stmt.where(Property.price >= filters["min_price"])
    if filters.get("max_price"):
        stmt = stmt.where(Property.price <= filters["max_price"])
    if filters.get("min_bedrooms"):
        stmt = stmt.where(Property.bedrooms >= filters["min_bedrooms"])
    if filters.get("exact_bedrooms") is not None:
        stmt = stmt.where(Property.bedrooms == filters["exact_bedrooms"])

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return total or 0, result.scalars().all()

async def get_property(db: AsyncSession, property_id: UUID) -> Property:
    prop = await db.scalar(select(Property).where(Property.id == property_id))
    if not prop:
        raise NotFoundError("Property not found")
    return prop

async def update_property(db: AsyncSession, property_id: UUID, data: PropertyUpdate) -> Property:
    prop = await get_property(db, property_id)
    
    if prop.status == "sold":
        raise ConflictError("Cannot update a property that has already been sold.")
        
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(prop, key, value)
        
    await db.commit()
    await db.refresh(prop)
    return prop

async def delete_property(db: AsyncSession, property_id: UUID):
    prop = await get_property(db, property_id)
    await db.delete(prop)
    await db.commit()