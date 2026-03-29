"""Message handling endpoints

Handles sending messages and retrieving conversation history
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from backend.api.main import get_container
from backend.core.container import ServiceContainer
from backend.core.models import SendMessageRequest, SendMessageResponse, SessionHistoryResponse

router = APIRouter()


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    container: ServiceContainer = Depends(get_container)
):
    """
    Send a message and get AI response

    Args:
        session_id: Session identifier
        request: Message request with content

    Returns:
        SendMessageResponse with AI response
    """
    engine = container.get_engine()
    memory_system = container.get_memory_system()

    # Send message and get response
    response = await engine.send_message(
        session_id=session_id,
        user_message=request.message
    )

    # Save to memory system
    await memory_system.save_message(
        session_id=session_id,
        user_id=request.user_id or "unknown",
        content=request.message,
        sender="user"
    )

    await memory_system.save_message(
        session_id=session_id,
        user_id=request.user_id or "unknown",
        content=response,
        sender="assistant"
    )

    return SendMessageResponse(
        session_id=session_id,
        response=response,
        timestamp=engine.sessions[session_id].messages[-1].get("timestamp") if engine.sessions[session_id].messages else None
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
