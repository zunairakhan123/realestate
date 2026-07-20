from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.leads.models import Lead, LeadStatus  # Ensure LeadStatus is imported
from app.leads.schemas import LeadCreate, LeadUpdate
from app.core.exceptions import ConflictError, NotFoundError
from app.core.events import event_bus
from app.core.websockets import manager

async def create_lead(db: AsyncSession, data: LeadCreate) -> Lead:
    lead = Lead(**data.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead

async def list_leads(db: AsyncSession, skip: int, limit: int, filters: dict):
    stmt = select(Lead)
    if filters.get("status"):
        stmt = stmt.where(Lead.status == filters["status"])
    if filters.get("agent_id"):
        stmt = stmt.where(Lead.agent_id == filters["agent_id"])
    if filters.get("customer_id"):
        stmt = stmt.where(Lead.customer_id == filters["customer_id"])
    if filters.get("property_id"):
        stmt = stmt.where(Lead.property_id == filters["property_id"])
    if filters.get("created_after"):
        stmt = stmt.where(Lead.created_at >= filters["created_after"])
    # Ensure this entire block is properly nested
    if filters.get("is_closed") is not None:
        terminal_statuses = [LeadStatus.won, LeadStatus.lost, LeadStatus.cancelled]
        if filters["is_closed"] is True:
            stmt = stmt.where(Lead.status.in_(terminal_statuses))
        else:
            stmt = stmt.where(Lead.status.not_in(terminal_statuses))
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return total, result.scalars().all()

async def get_lead_detail(db: AsyncSession, lead_id: UUID) -> Lead:
    stmt = select(Lead).where(Lead.id == lead_id).options(
        selectinload(Lead.customer), selectinload(Lead.property)
    )
    lead = await db.scalar(stmt)
    if not lead:
        raise NotFoundError("Lead not found")
    return lead

async def update_lead(db: AsyncSession, lead_id: UUID, data: LeadUpdate) -> Lead:
    # 1. Fetch the lead (This handles the 404 check automatically)
    lead = await get_lead_detail(db, lead_id)
    
    # 2. BUSINESS RULE: Check original state BEFORE applying updates
    terminal_states = ["won", "lost", "cancelled"]
    if lead.status.value in terminal_states and data.status and data.status.value not in terminal_states:
        raise ConflictError(f"Cannot move a closed lead ({lead.status.value}) back to an active state.")
    
    # 3. Apply updates safely
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, key, value)
        
    await db.commit()
    await db.refresh(lead)
    
    # 4. EVENT BUS: Emit notification if newly moved to a terminal status
    if data.status and data.status.value in terminal_states:
        payload = {
            "id": str(lead.id),
            "status": lead.status.value,
            "agent_id": str(lead.agent_id)
        }
        event_bus.emit("lead_terminal_status", payload)
    # FIRE THE WEBSOCKET BROADCAST
    if data.status:
        await manager.broadcast_lead_update(
            str(lead.id), 
            {
                "event": "status_changed", 
                "lead_id": str(lead.id), 
                "new_status": lead.status.value
            }
        )
        
    return lead


async def delete_lead(db: AsyncSession, lead_id: UUID):
    lead = await db.scalar(select(Lead).where(Lead.id == lead_id))
    if not lead:
        raise NotFoundError("Lead not found")
    await db.delete(lead)
    await db.commit()
