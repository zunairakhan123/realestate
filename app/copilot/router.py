"""
AI Copilot Router

This module exposes the REST API used by the frontend
to communicate with the enterprise AI Copilot.

Responsibilities:
    • Authentication
    • Request validation
    • Dependency injection
    • Request ID propagation
    • Calling the service layer

No business logic should live here.
"""

from typing import List
from typing import Optional
import uuid

from fastapi import (
    APIRouter,
    Depends,
    Header,
    status,
)

from pydantic import (
    BaseModel,
    Field,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.auth.models import User
from app.core.auth import get_current_user
from app.copilot.service import process_copilot_request

# =============================================================================
# Router
# =============================================================================

router = APIRouter(
    prefix="/copilot",
    tags=["AI Copilot"],
)

# =============================================================================
# Request Models
# =============================================================================


class ChatMessage(BaseModel):
    """
    Represents one previous chat message.

    Used to support multi-turn conversations.
    """

    role: str = Field(
        ...,
        description="user | assistant | tool | system",
    )

    content: str = Field(
        ...,
        description="Message content",
    )


class CopilotChatRequest(BaseModel):
    """
    Request body received from frontend.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Current user prompt.",
    )

    history: List[ChatMessage] = Field(
        default_factory=list,
        description="Previous conversation.",
    )


# =============================================================================
# Response Model
# =============================================================================


class CopilotChatResponse(BaseModel):
    """
    Standard response returned to frontend.
    """

    response: str

    tool_executed: bool

    request_id: str


# =============================================================================
# Endpoint
# =============================================================================


@router.post(
    "/chat",
    response_model=CopilotChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with AI Copilot",
    description="""
Enterprise AI Copilot endpoint.

Supports:

• Multi-turn conversation

• Tool Calling

• RBAC

• Backend Service Execution

• Conversation History

• Request Tracing
""",
)
async def chat_with_copilot(
    payload: CopilotChatRequest,

    db: AsyncSession = Depends(get_db),

    current_user: User = Depends(get_current_user),

    x_request_id: Optional[str] = Header(
        default=None,
        alias="X-Request-ID",
    ),
):
    """
    Main AI Copilot endpoint.

    Authentication is mandatory.

    The authenticated user's role determines
    what the AI is allowed to do.

    The AI itself NEVER bypasses RBAC.
    """

    request_id = x_request_id or str(uuid.uuid4())

    history = [
        message.model_dump()
        for message in payload.history
    ]

    result = await process_copilot_request(
        db=db,

        current_user=current_user,

        user_message=payload.message,

        conversation_history=history,

        request_id=request_id,
    )

    return CopilotChatResponse(
        response=result["response"],
        tool_executed=result["tool_executed"],
        request_id=request_id,
    )