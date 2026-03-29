"""Authentication endpoints for JWT token generation

Provides endpoints for users to obtain JWT tokens for API access.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging

from backend.core.auth import get_jwt_handler

logger = logging.getLogger(__name__)

router = APIRouter()


class TokenRequest(BaseModel):
    """Request model for token generation"""
    user_id: str


class TokenResponse(BaseModel):
    """Response model for token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/auth/token", response_model=TokenResponse)
async def get_token(request: TokenRequest):
    """
    Generate JWT token for API access

    Args:
        request: TokenRequest with user_id

    Returns:
        JWT token for API authentication

    Note:
        In production, this endpoint should require actual user authentication.
        For now, it accepts any user_id for development.
    """
    if not request.user_id or len(request.user_id) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required"
        )

    try:
        jwt_handler = get_jwt_handler()
        token = jwt_handler.create_token(
            user_id=request.user_id,
            expires_in_hours=24
        )

        logger.info(f"JWT token generated for user {request.user_id}")

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=86400  # 24 hours in seconds
        )
    except Exception as e:
        logger.error(f"Failed to generate token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authentication token"
        )
