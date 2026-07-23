"""
AI Copilot Service

This module is the brain of the AI assistant.

Flow:

Frontend
      │
      ▼
POST /copilot/chat
      │
      ▼
Router
      │
      ▼
process_copilot_request()
      │
      ▼
Ollama
      │
      ▼
Tool Selection
      │
      ▼
Backend Service Layer
      │
      ▼
Database
      │
      ▼
LLM summarizes tool results
      │
      ▼
Frontend


IMPORTANT

The LLM NEVER accesses the database.

Every action goes through:

LLM
 ↓
Tool
 ↓
Service Layer
 ↓
Database

This guarantees:

• RBAC
• Validation
• Business Rules
• Event Listeners
• Notifications
• Logging
"""

from __future__ import annotations

import json
import os
import time

from typing import Any
from typing import Dict
from typing import List

import httpx

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.logger import logger
from app.copilot.tools import (
    COPILOT_TOOLS_SCHEMA,
    TOOL_DISPATCH_MAP,
)

# =============================================================================
# Configuration
# =============================================================================

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "https://newcastle-mothers-themes-billion.trycloudflare.com",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen3:8b",
)

OLLAMA_TIMEOUT = float(
    os.getenv(
        "OLLAMA_TIMEOUT",
        "600"
    )
)

# =============================================================================
# System Prompt
# =============================================================================

SYSTEM_PROMPT = """
You are RealtyCRM AI Copilot.

You are connected to backend tools.

You MUST NEVER fabricate:

- Customer IDs
- Property IDs
- Lead IDs
- Database records

If information is required,
execute the appropriate tool.

Never bypass role permissions.

Never expose SQL.

Never expose stack traces.

Never invent results.

Always answer using tool results.

You have access to backend tools: list_properties, update_lead_status, get_user_leads, get_customer.

If the user request requires a tool, you MUST respond ONLY with a JSON block in this exact format, with no extra text:
{"tool": "tool_name", "arguments": {"arg_name": "value"}}

If no tool is required, respond normally in plain text.

Be concise.

Be professional.
"""
# =============================================================================
# Tool Executor
# =============================================================================

async def execute_tool(
    *,
    db: AsyncSession,
    current_user: User,
    tool_name: str,
    arguments: Dict[str, Any],
    request_id: str,
) -> str:
    """
    Executes one backend tool.

    This function is responsible for:

    • validating tool exists
    • audit logging
    • timing execution
    • serializing results
    • preventing crashes
    """

    start = time.perf_counter()

    if tool_name not in TOOL_DISPATCH_MAP:

        logger.warning(
            f"[{request_id}] Unknown tool requested: {tool_name}"
        )

        return json.dumps(
            {
                "error": f"Unknown tool '{tool_name}'."
            }
        )

    logger.info(
        (
            f"[{request_id}] "
            f"Executing Tool={tool_name} "
            f"User={current_user.id} "
            f"Role={current_user.role}"
        )
    )

    try:

        tool = TOOL_DISPATCH_MAP[tool_name]

        result = await tool(
            db=db,
            current_user=current_user,
            args=arguments,
        )

        duration = (
            time.perf_counter() - start
        ) * 1000

        logger.info(
            (
                f"[{request_id}] "
                f"Finished Tool={tool_name} "
                f"in {duration:.2f}ms"
            )
        )

        return json.dumps(result)

    except Exception as exc:

        # === PRINT THE REAL PYTHON TRACEBACK DIRECTLY TO TERMINAL ===
        import traceback
        traceback.print_exc()

        logger.exception(
            f"[{request_id}] Tool failed: {tool_name}"
        )

        return json.dumps(
            {
                "error": str(exc)
            }
        )
# =============================================================================
# First LLM Call
# =============================================================================

async def ask_llm_for_plan(
    *,
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    prompt_builder = ""
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        prompt_builder += f"\n{role.upper()}: {content}"
    
    prompt_builder += "\nASSISTANT:"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt_builder,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        response = await client.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        raw_text = data.get("response", "").strip()

        # Try to parse if the model outputted a tool call JSON block
        tool_calls = []
        try:
            if raw_text.startswith("{") and "tool" in raw_text:
                parsed = json.loads(raw_text)
                if "tool" in parsed:
                    tool_calls = [{
                        "function": {
                            "name": parsed["tool"],
                            "arguments": parsed.get("arguments", {})
                        }
                    }]
        except Exception:
            pass

        return {
            "message": {
                "role": "assistant",
                "content": raw_text,
                "tool_calls": tool_calls
            }
        }
# =============================================================================
# Execute Tool Calls Returned by Ollama
# =============================================================================

async def execute_tool_calls(
    *,
    db: AsyncSession,
    current_user: User,
    tool_calls: List[Dict[str, Any]],
    messages: List[Dict[str, Any]],
    request_id: str,
) -> None:
    """
    Executes every tool requested by the LLM.

    Each tool result is appended back into the conversation
    so the LLM can use the data when generating the final reply.

    This function modifies 'messages' in-place.
    """

    for tool_call in tool_calls:

        function = tool_call.get("function", {})

        tool_name = function.get("name")

        raw_arguments = function.get("arguments", {})

        # Ollama sometimes returns arguments as JSON string
        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments)
            except Exception:
                arguments = {}
        else:
            arguments = raw_arguments

        logger.info(
            f"[{request_id}] LLM requested tool '{tool_name}'"
        )

        tool_output = await execute_tool(
            db=db,
            current_user=current_user,
            tool_name=tool_name,
            arguments=arguments,
            request_id=request_id,
        )

        # Feed tool output back into the conversation
        messages.append(
            {
                "role": "tool",
                "name": tool_name,
                "content": tool_output,
            }
        )
# =============================================================================
# Final Response Generation
# =============================================================================

async def generate_final_response(
    *,
    messages: List[Dict[str, Any]],
) -> str:
    """
    Synthesizes the final answer using the /api/generate endpoint.
    """
    prompt_builder = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        prompt_builder += f"\n{role.upper()}: {content}"
    
    prompt_builder += "\nASSISTANT (Provide a friendly, human-readable summary of the tool results above):"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt_builder,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        response = await client.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
        )

        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
# =============================================================================
# Main Copilot Pipeline
# =============================================================================

async def process_copilot_request(
    *,
    db: AsyncSession,
    current_user: User,
    user_message: str,
    conversation_history: List[Dict[str, Any]],
    request_id: str,
) -> Dict[str, Any]:
    """
    Main orchestration pipeline.

    Flow

    User
      ↓

    Ollama

      ↓

    Tool Selection

      ↓

    Execute Backend Services

      ↓

    Feed Results to Ollama

      ↓

    Final Answer
    """

    messages: List[Dict[str, Any]] = [

        {
            "role": "system",
            "content":
                SYSTEM_PROMPT
                + f"\nCurrent Role: {current_user.role}"
        }

    ]

    messages.extend(conversation_history)

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    logger.info(
        f"[{request_id}] Starting Copilot request"
    )

    try:

        first_response = await ask_llm_for_plan(
            history=messages,
        )

        assistant_message = (
            first_response
            .get("message", {})
        )

        messages.append(assistant_message)

        tool_calls = assistant_message.get(
            "tool_calls",
            [],
        )

        # --------------------------
        # No tool required
        # --------------------------

        if not tool_calls:

            logger.info(
                f"[{request_id}] No tool execution required."
            )

            return {

                "response":
                    assistant_message.get(
                        "content",
                        "",
                    ),

                "tool_executed": False,
            }

        # --------------------------
        # Execute requested tools
        # --------------------------

        await execute_tool_calls(

            db=db,

            current_user=current_user,

            tool_calls=tool_calls,

            messages=messages,

            request_id=request_id,
        )

        logger.info(
            f"[{request_id}] Tool execution completed."
        )

        # --------------------------
        # Final AI Response
        # --------------------------

        final_answer = await generate_final_response(
            messages=messages,
        )

        return {

            "response": final_answer,

            "tool_executed": True,
        }

    except httpx.TimeoutException:

        logger.exception(
            f"[{request_id}] Ollama timeout"
        )

        return {

            "response":
                "The AI model took too long to respond.",

            "tool_executed": False,
        }

    except httpx.HTTPError:

        logger.exception(
            f"[{request_id}] Ollama HTTP error"
        )

        return {

            "response":
                "Unable to communicate with the AI service.",

            "tool_executed": False,
        }

    except Exception:

        logger.exception(
            f"[{request_id}] Unexpected Copilot error"
        )

        return {

            "response":
                "An internal server error occurred while processing your request.",

            "tool_executed": False,
        }
