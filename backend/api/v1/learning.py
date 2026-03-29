"""Learning and feedback endpoints

Handles learning records, feedback collection, and effectiveness tracking
"""

from fastapi import APIRouter, Depends
from typing import Optional

from backend.api.main import get_container
from backend.core.container import ServiceContainer
from backend.core.models import LearningReportResponse

router = APIRouter()


@router.post("/sessions/{session_id}/feedback")
async def submit_feedback(
    session_id: str,
    rating: int,
    feedback_text: Optional[str] = None,
    container: ServiceContainer = Depends(get_container)
):
    """
    Submit quality feedback on AI response

    Args:
        session_id: Session identifier
        rating: Quality rating (1-5 stars)
        feedback_text: Optional detailed feedback

    Returns:
        Status message
    """
    learning_system = container.get_learning_system()
    engine = container.get_engine()

    # Verify session exists
    if session_id not in engine.sessions:
        from backend.core.exceptions import SessionNotFoundError
        raise SessionNotFoundError(f"Session {session_id} not found")

    # Process feedback
    await learning_system.process_user_feedback(
        session_id=session_id,
        rating=rating,
        feedback_text=feedback_text
    )

    return {
        "session_id": session_id,
        "rating": rating,
        "processed": True
    }


@router.get("/pai/{pai_instance_id}/learning", response_model=LearningReportResponse)
async def get_learning_report(
    pai_instance_id: str,
    container: ServiceContainer = Depends(get_container)
):
    """
    Get learning progress report for a PAI instance

    Args:
        pai_instance_id: PAI instance identifier

    Returns:
        LearningReportResponse with effectiveness metrics
    """
    learning_system = container.get_learning_system()

    # Get learning effectiveness
    report = await learning_system.get_learning_effectiveness_report(pai_instance_id)

    return report


@router.get("/users/{user_id}/learning-preferences")
async def get_learning_preferences(
    user_id: str,
    container: ServiceContainer = Depends(get_container)
):
    """
    Get learned preferences for a user

    Args:
        user_id: User identifier

    Returns:
        Learned preferences and patterns
    """
    learning_system = container.get_learning_system()

    # Get preferences
    preferences = await learning_system.get_learned_preferences(user_id)

    return {
        "user_id": user_id,
        "preferences": preferences if preferences else [],
        "count": len(preferences) if preferences else 0
    }


@router.get("/pai/{pai_instance_id}/patterns")
async def get_success_patterns(
    pai_instance_id: str,
    container: ServiceContainer = Depends(get_container)
):
    """
    Get success patterns for a PAI instance

    Args:
        pai_instance_id: PAI instance identifier

    Returns:
        List of detected patterns
    """
    learning_system = container.get_learning_system()

    # Get patterns
    patterns = await learning_system.get_success_patterns(pai_instance_id)

    return {
        "pai_instance_id": pai_instance_id,
        "patterns": patterns if patterns else [],
        "count": len(patterns) if patterns else 0
    }
