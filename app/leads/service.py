from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.customers.models import Customer
from app.leads.models import Lead, LeadStatus
from app.leads.schemas import LeadCreate, LeadUpdate
from app.core.exceptions import ConflictError, NotFoundError, BusinessRuleViolation
from app.core.events import event_bus
from app.core.websockets import manager
from app.properties.models import Property

async def create_lead_from_customer(
    db: AsyncSession, 
    user_id: UUID,  # Changed parameter semantic from user_id to resolve to customer profile
    payload: LeadCreate
) -> Lead:
    """
    Automatically resolves the customer profile from the authenticated user ID,
    inherits the agent_id from the selected property, 
    and binds it for lead creation.
    Emits LeadCreatedEvent.
    """
    # 1. Resolve the customer profile ID using the authenticated user_id
    customer_record = await db.scalar(
        select(Customer).where(Customer.user_id == user_id)
    )
    if not customer_record:
        raise NotFoundError("Customer profile not found for the authenticated user.")

    # 2. Fetch property details to inherit the agent_id
    property_record = await db.scalar(
        select(Property).where(Property.id == payload.property_id)
    )
    if not property_record:
        raise NotFoundError(f"Property with ID {payload.property_id} not found.")

    # 3. Create the lead binding the resolved customers.id foreign key
    new_lead = Lead(
        customer_id=customer_record.id,           # Resolved from the customers table primary key
        property_id=payload.property_id,          # From customer selection
        agent_id=property_record.agent_id,          # Inherited directly from the property
        status=LeadStatus.new                     # Initial status rule: NEW
    )

    db.add(new_lead)
    await db.commit()
    await db.refresh(new_lead)
    
    # Emit LeadCreatedEvent for notification listener integration
    event_bus.emit("LeadCreatedEvent", {
        "lead_id": str(new_lead.id),
        "customer_id": str(new_lead.customer_id),
        "agent_id": str(new_lead.agent_id)
    })
    
    return new_lead

# async def list_leads(db: AsyncSession, skip: int, limit: int, filters: dict):
#     stmt = select(Lead)
#     if filters.get("status"):
#         stmt = stmt.where(Lead.status == filters["status"])
#     if filters.get("agent_id"):
#         stmt = stmt.where(Lead.agent_id == filters["agent_id"])
#     if filters.get("customer_id"):
#         stmt = stmt.where(Lead.customer_id == filters["customer_id"])
#     if filters.get("property_id"):
#         stmt = stmt.where(Lead.property_id == filters["property_id"])
#     if filters.get("created_after"):
#         stmt = stmt.where(Lead.created_at >= filters["created_after"])
        
#     if filters.get("is_closed") is not None:
#         terminal_statuses = [LeadStatus.closed]
#         if filters["is_closed"] is True:
#             stmt = stmt.where(Lead.status.in_(terminal_statuses))
#         else:
#             stmt = stmt.where(Lead.status.not_in(terminal_statuses))
            
#     total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
#     stmt = stmt.offset(skip).limit(limit)
#     result = await db.execute(stmt)
#     return total or 0, result.scalars().all()

async def list_leads(db: AsyncSession, skip: int, limit: int, filters: dict, current_user = None):
    stmt = select(Lead)
    
    # Normalize current_user.role to handle both Enum or String safely (case-insensitive or exact match)
    if current_user and current_user.role:
        role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        
        # If the user is an agent, restrict leads strictly to their agent_id
        if role_val.upper() == "AGENT":
            stmt = stmt.where(Lead.agent_id == current_user.id)
        elif role_val.upper() == "CUSTOMER":
            # Optional: ensure customers only see their own leads here as well if queried directly
            customer_record = await db.scalar(select(Customer).where(Customer.user_id == current_user.id))
            if customer_record:
                stmt = stmt.where(Lead.customer_id == customer_record.id)
            else:
                stmt = stmt.where(Lead.customer_id == None) # No leads if profile missing
    
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
        
    if filters.get("is_closed") is not None:
        terminal_statuses = [LeadStatus.closed]
        if filters["is_closed"] is True:
            stmt = stmt.where(Lead.status.in_(terminal_statuses))
        else:
            stmt = stmt.where(Lead.status.not_in(terminal_statuses))
            
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return total or 0, result.scalars().all()

async def get_lead_detail(db: AsyncSession, lead_id: UUID) -> Lead:
    stmt = select(Lead).where(Lead.id == lead_id).options(
        selectinload(Lead.customer), selectinload(Lead.property)
    )
    lead = await db.scalar(stmt)
    if not lead:
        raise NotFoundError("Lead not found")
    return lead

async def update_lead(db: AsyncSession, lead_id: UUID, data: LeadUpdate) -> Lead:
    lead = await get_lead_detail(db, lead_id)
    
    # BUSINESS RULE VALIDATION: Once status becomes QUALIFIED, it must NEVER return to NEW.
    if data.status and lead.status == LeadStatus.qualified and data.status == LeadStatus.new:
        raise BusinessRuleViolation("Once a lead status becomes QUALIFIED, it must never return to NEW.")
    
    old_status = lead.status
    
    # Apply updates safely
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, key, value)
        
    await db.commit()
    await db.refresh(lead)
    
    # Event and notification trigger if lead has newly become QUALIFIED
    if old_status != LeadStatus.qualified and lead.status == LeadStatus.qualified:
        event_bus.emit("LeadQualifiedEvent", {
            "lead_id": str(lead.id),
            "customer_id": str(lead.customer_id),
            "agent_id": str(lead.agent_id)
        })

    # WebSocket Real-Time Broadcast
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

async def update_lead_status(db: AsyncSession, lead_id: UUID, new_status: str):
    lead = await get_lead_detail(db, lead_id)
    if not lead:
        raise ValueError("Lead not found")
        
    old_status = lead.status
    
    # Update status in database
    lead.status = new_status
    await db.commit()
    await db.refresh(lead)
    
    # Build payload including old_status
    lead_data = {
        "id": str(lead.id),
        "old_status": str(old_status),
        "status": str(lead.status),
        "agent_id": str(lead.agent_id),
        "customer_id": str(lead.customer_id)
    }

    # Trigger notification event if status actually changed
    if old_status != lead.status:
        event_bus.emit("lead_status_changed", lead_data)
        
        if lead.status in ["sold", "closed", "lost"]:
            event_bus.emit("lead_terminal", lead_data)

    # Broadcast real-time update via WebSocket
    await manager.broadcast_lead_update(str(lead.id), {
        "event": "lead_status_updated",
        "data": lead_data
    })
    
    return lead

async def delete_lead(db: AsyncSession, lead_id: UUID):
    lead = await db.scalar(select(Lead).where(Lead.id == lead_id))
    if not lead:
        raise NotFoundError("Lead not found")
    await db.delete(lead)
    await db.commit()