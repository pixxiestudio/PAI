"""Message handling endpoints

Handles sending messages and retrieving conversation history
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import Optional
from datetime import datetime, timezone

from backend.api.main import get_container
from backend.core.container import ServiceContainer
from backend.core.models import SendMessageRequest, SendMessageResponse, SessionHistoryResponse
from backend.api.middleware.auth import get_current_user

router = APIRouter()


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    current_user: str = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """
    Send a message and get AI response

    Args:
        session_id: Session identifier
        request: Message request with content
        current_user: Authenticated user ID from JWT token

    Returns:
        SendMessageResponse with AI response
    """
    engine = container.get_engine()
    memory_system = container.get_memory_system()
    learning_system = container.get_learning_system()

    # Build context injection from memory (Layer 3)
    context = await memory_system.build_injection_context(
        session_id=session_id,
        user_id=current_user
    )

    # Send message and get response with context
    response = await engine.send_message(
        session_id=session_id,
        user_message=request.message,
        context_injection=context if context else request.context_injection,
        model=request.model
    )

    # Save to memory system with authenticated user ID
    await memory_system.save_message(
        session_id=session_id,
        user_id=current_user,
        content=request.message,
        sender="user"
    )

    await memory_system.save_message(
        session_id=session_id,
        user_id=current_user,
        content=response,
        sender="assistant"
    )

    # Record learning outcome for feedback loop traceability
    pai_instance_id = "default"
    if session_id in engine.sessions:
        pai_instance_id = engine.sessions[session_id].pai_instance_id

    await learning_system.record_interaction_outcome(
        pai_instance_id=pai_instance_id,
        interaction_type="message",
        input_data={"message": request.message[:200]},
        output_data={"response": response[:200]},
        success=True,
        quality_score=0.0,
        session_id=session_id,
        user_id=current_user
    )

    return SendMessageResponse(
        session_id=session_id,
        response=response,
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    container: ServiceContainer = Depends(get_container)
):
    """
    Get conversation history for a session

    Args:
        session_id: Session identifier

    Returns:
        SessionHistoryResponse with message history
    """
    engine = container.get_engine()

    # Get history
    history = await engine.get_session_history(session_id)

    return SessionHistoryResponse(
        session_id=session_id,
        messages=history,
        total=len(history)
    )


@router.get("/sessions/{session_id}/messages")
async def get_paginated_messages(
    session_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    container: ServiceContainer = Depends(get_container)
):
    """
    Get paginated message history

    Args:
        session_id: Session identifier
        skip: Number of messages to skip
        limit: Maximum messages to return

    Returns:
        Paginated message list
    """
    engine = container.get_engine()

    # Get history
    history = await engine.get_session_history(session_id)

    # Apply pagination
    start = skip
    end = skip + limit
    paginated = history[start:end]

    return {
        "session_id": session_id,
        "messages": paginated,
        "skip": skip,
        "limit": limit,
        "total": len(history)
    }
