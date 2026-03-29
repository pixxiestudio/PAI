"""Memory management endpoints

Handles memory retrieval, saving, and updates
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, List

from backend.api.main import get_container
from backend.core.container import ServiceContainer
from backend.core.models import SaveMemoryRequest, SaveMemoryResponse, GetMemoriesResponse, MemoryEntryResponse

router = APIRouter()


@router.get("/users/{user_id}/memories", response_model=GetMemoriesResponse)
async def get_user_memories(
    user_id: str,
    memory_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    container: ServiceContainer = Depends(get_container)
):
    """
    Get user's memories

    Args:
        user_id: User identifier
        memory_type: Filter by memory type (semantic, episodic, session)
        limit: Maximum memories to return

    Returns:
        GetMemoriesResponse with user's memories
    """
    memory_system = container.get_memory_system()

    # Get relevant memories
    memories = await memory_system.get_relevant_memories(
        user_id=user_id,
        limit=limit
    )

    # Filter by type if specified
    if memory_type:
        memories = [m for m in memories if hasattr(m, 'memory_type') and m.memory_type == memory_type]

    return GetMemoriesResponse(
        user_id=user_id,
        memories=memories,
        total=len(memories)
    )


@router.post("/users/{user_id}/memories", response_model=SaveMemoryResponse)
async def save_memory(
    user_id: str,
    request: SaveMemoryRequest,
    container: ServiceContainer = Depends(get_container)
):
    """
    Save a new memory

    Args:
        user_id: User identifier
        request: Memory save request

    Returns:
        SaveMemoryResponse with memory ID
    """
    memory_system = container.get_memory_system()

    # Save memory
    memory_id = await memory_system.save_memory(
        user_id=user_id,
        content=request.content,
        memory_type=request.memory_type,
        importance=request.importance or 1.0
    )

    return SaveMemoryResponse(
        memory_id=memory_id,
        user_id=user_id,
        created=True
    )


@router.put("/memories/{memory_id}")
async def update_memory_importance(
    memory_id: str,
    importance: float = Query(..., ge=0.0, le=1.0),
    container: ServiceContainer = Depends(get_container)
):
    """
    Update memory importance score

    Args:
        memory_id: Memory identifier
        importance: New importance score (0.0-1.0)

    Returns:
        Status message
    """
    memory_system = container.get_memory_system()

    # Update importance
    await memory_system.update_memory_importance(memory_id, importance)

    return {
        "memory_id": memory_id,
        "importance": importance,
        "updated": True
    }


@router.get("/sessions/{session_id}/context")
async def get_session_context(
    session_id: str,
    container: ServiceContainer = Depends(get_container)
):
    """
    Get context injection for a session (Layer 3 memory)

    Args:
        session_id: Session identifier

    Returns:
        Context string for injection into prompts
    """
    memory_system = container.get_memory_system()

    # Build context
    context = await memory_system.get_session_context(session_id)

    return {
        "session_id": session_id,
        "context": context,
        "token_estimate": len(context) // 4  # Rough token estimate
    }
