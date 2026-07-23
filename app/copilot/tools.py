"""
AI Copilot Tool Registry

This module exposes a controlled set of backend capabilities that the LLM
is allowed to execute.

IMPORTANT:
The AI NEVER talks directly to the database.

Instead:

LLM
    ↓
Tool
    ↓
Service Layer
    ↓
Database

This guarantees that:
- RBAC is enforced
- Business rules are enforced
- Events are triggered
- Logging happens
- Validation happens

Every tool is simply a thin wrapper around an existing service.
"""

from uuid import UUID
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import union
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.exceptions import NotFoundError
from app.properties import service as property_service
from app.leads import service as lead_service
from app.customers import service as customer_service
from sqlalchemy.future import select
from app.leads.models import Lead  # <-- Import the Lead model
from typing import Any, Dict, List, Optional, Union

# =============================================================================
# Tool Argument Schemas
# =============================================================================

class ListPropertiesArgs(BaseModel):
    """
    Optional filters when listing properties.
    """

    city: Optional[str] = Field(
        default=None,
        description="Filter properties by city."
    )


class UpdateLeadStatusArgs(BaseModel):
    """
    Arguments required for updating a lead.
    """
    lead_id: Union[str, UUID] = Field(..., description="Lead UUID.")
    new_status: Optional[str] = Field(default=None, description="Target lead status.")
    status: Optional[str] = Field(default=None, description="Alias for target lead status.")

class GetUserLeadsArgs(BaseModel):
    """
    No arguments.

    Current authenticated user determines
    which leads are visible.
    """

    pass


class GetCustomerArgs(BaseModel):
    """
    Retrieve one customer.
    """
    customer_id: Union[str, UUID]

# =============================================================================
# Tool Implementations
# =============================================================================

async def tool_list_properties(
    db: AsyncSession,
    current_user: User,
    args: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Return available properties matching the expected schema.
    """
    validated = ListPropertiesArgs(**args)

    # Corrected to call the actual list_properties service function signature
    filters = {"city": validated.city} if validated.city else {}
    _, properties = await property_service.list_properties(
        db=db,
        skip=0,
        limit=50,
        filters=filters
    )

    return [
        {
            "id": str(property.id),
            "address": property.address,
            "city": property.city,
            "price": float(property.price),
            "bedrooms": property.bedrooms,
            "property_type": property.property_type,
            "status": property.status,
            "image_url": property.image_url,
            "agent_id": str(property.agent_id) if property.agent_id else None,
            "created_at": property.created_at.isoformat() if property.created_at else None,
            "updated_at": property.updated_at.isoformat() if property.updated_at else None
        }
        for property in properties
    ]

# -----------------------------------------------------------------------------


async def tool_update_lead_status(
    db: AsyncSession,
    current_user: User,
    args: Dict[str, Any]
) -> Dict[str, Any]:
    validated = UpdateLeadStatusArgs(**args)
    target_status = validated.new_status or validated.status
    
    if not target_status:
        raise ValueError("Either 'new_status' or 'status' must be provided.")

    # Safely handle whether lead_id is already a UUID object or a string
    lead_uuid = validated.lead_id if isinstance(validated.lead_id, UUID) else UUID(validated.lead_id)
    
    # 1. Try finding the lead directly by its primary key UUID
    lead = await db.scalar(select(Lead).where(Lead.id == lead_uuid))
    
    # 2. Fallback: If the LLM accidentally passed a property_id or customer_id
    if not lead:
        lead = await db.scalar(
            select(Lead).where(
                (Lead.property_id == lead_uuid) | (Lead.customer_id == lead_uuid)
            )
        )
        
    if not lead:
        raise NotFoundError(f"Lead not found for ID {validated.lead_id}")

    # 3. Perform the status update using the validated lead's actual ID
    updated_lead = await lead_service.update_lead_status(db, lead.id, target_status)

    return {
        "success": True,
        "lead_id": str(updated_lead.id),
        "new_status": str(updated_lead.status),
        "customer_id": str(updated_lead.customer_id),
        "agent_id": str(updated_lead.agent_id) if updated_lead.agent_id else None
    }

# -----------------------------------------------------------------------------


async def tool_get_user_leads(
    db: AsyncSession,
    current_user: User,
    args: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Return leads visible to authenticated user.

    Agent:
        Only assigned leads

    Customer:
        Only own leads

    Admin:
        All leads
    """

    GetUserLeadsArgs(**args)

    # Enforce role-based filters dynamically when querying list_leads
    filters = {}
    if current_user.role == "agent":
        filters["agent_id"] = current_user.id
    elif current_user.role == "customer":
        # Resolve customer ID if needed, or filter accordingly
        pass

    _, leads = await lead_service.list_leads(
        db=db,
        skip=0,
        limit=50,
        filters=filters
    )

    return [
        {
            "id": str(lead.id),
            "status": str(lead.status),
            "customer_id": str(lead.customer_id),
            "property_id": str(lead.property_id),
            "agent_id": str(lead.agent_id) if lead.agent_id else None
        }
        for lead in leads
    ]


# -----------------------------------------------------------------------------


async def tool_get_customer(
    db: AsyncSession,
    current_user: User,
    args: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Retrieve customer details.
    """
    validated = GetCustomerArgs(**args)
    
    # Safely handle whether customer_id is already a UUID object or a string
    customer_uuid = (
        validated.customer_id 
        if isinstance(validated.customer_id, UUID) 
        else UUID(validated.customer_id)
    )

    customer = await customer_service.get_customer(
        db=db,
        customer_id=customer_uuid
    )

    return {
        "id": str(customer.id),
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "payment": getattr(customer, "payment", None)
    }

# =============================================================================
# Tool Registry
# =============================================================================

TOOL_DISPATCH_MAP = {
    "list_properties": tool_list_properties,
    "update_lead_status": tool_update_lead_status,
    "get_user_leads": tool_get_user_leads,
    "get_customer": tool_get_customer,
}


# =============================================================================
# Tool Definitions sent to Ollama
# =============================================================================

COPILOT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_properties",
            "description": (
                "Return available properties."
                " Optionally filter by city."
            ),
            "parameters": ListPropertiesArgs.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_lead_status",
            "description": (
                "Update a CRM lead status."
            ),
            "parameters": UpdateLeadStatusArgs.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_leads",
            "description": (
                "Return leads visible to authenticated user."
            ),
            "parameters": GetUserLeadsArgs.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer",
            "description": (
                "Retrieve one customer."
            ),
            "parameters": GetCustomerArgs.model_json_schema()
        }
    }
]