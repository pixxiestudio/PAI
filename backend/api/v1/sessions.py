"""Session management endpoints

Handles session creation, retrieval, and termination
"""

from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone
from typing import Optional

from backend.api.main import get_container
from backend.core.container import ServiceContainer
from backend.core.models import SessionResponse
from backend.core.exceptions import SessionNotFoundError

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    user_id: str,
    pai_instance_id: Optional[str] = None,
    session_type: str = "chat",
    container: ServiceContainer = Depends(get_container)
):
    """
    Create a new conversation session

    Args:
        user_id: User identifier
        pai_instance_id: PAI instance ID (defaults to "default")
        session_type: Type of session (chat, skill_execution, debate, learning)

    Returns:
        SessionResponse with session_id and details
    """
    engine = container.get_engine()

    # Create session
    session_id = await engine.create_session(
        user_id=user_id,
        pai_instance_id=pai_instance_id or "default",
        session_type=session_type
    )

    return SessionResponse(
        session_id=session_id,
        user_id=user_id,
        pai_instance_id=pai_instance_id or "default",
        created_at=datetime.now(timezone.utc),
        session_type=session_type
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    container: ServiceContainer = Depends(get_container)
):
    """
    Get session details

    Args:
        session_id: Session identifier

    Returns:
        SessionResponse with session details
    """
    engine = container.get_engine()

    # Verify session exists
    if session_id not in engine.sessions:
        raise SessionNotFoundError(f"Session {session_id} not found")

    context = engine.sessions[session_id]

    return SessionResponse(
        session_id=session_id,
        user_id="unknown",  # Would need to track from database
        pai_instance_id=context.pai_instance_id,
        created_at=datetime.now(timezone.utc),
        session_type="chat",
        message_count=len(context.messages)
    )


@router.delete("/sessions/{session_id}")
async def end_session(
    session_id: str,
    container: ServiceContainer = Depends(get_container)
):
    """
    End a conversation session

    Args:
        session_id: Session identifier

    Returns:
        Status message
    """
    engine = container.get_engine()

    # End session
    await engine.end_session(session_id)

    return {"status": "ended", "session_id": session_id}


@router.get("/sessions", response_model=dict)
async def list_sessions(
    user_id: Optional[str] = Query(None),
    pai_instance_id: Optional[str] = Query(None),
    container: ServiceContainer = Depends(get_container)
):
    """
    List active sessions (optionally filtered by user or PAI instance)

    Args:
        user_id: Filter by user ID
        pai_instance_id: Filter by PAI instance ID

    Returns:
        List of active sessions
    """
    engine = container.get_engine()

    # Get all active sessions
    sessions = []
    for session_id, context in engine.sessions.items():
        # Apply filters if provided
        if pai_instance_id and context.pai_instance_id != pai_instance_id:
            continue

        sessions.append({
            "session_id": session_id,
            "pai_instance_id": context.pai_instance_id,
            "message_count": len(context.messages),
            "model": context.model
        })

    return {"sessions": sessions, "total": len(sessions)}
