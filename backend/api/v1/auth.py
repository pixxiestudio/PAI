"""Authentication endpoints for JWT token generation and logout

Provides endpoints for users to obtain JWT tokens for API access
and revoke tokens on logout.
"""

from fastapi import APIRouter, HTTPException, Request, status
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
        In production, this endpoint should require actual user authentication
        (password, OAuth, etc.). For now, it accepts any user_id for development.
        Per-user rate limiting is applied to prevent account enumeration.
    """
    from backend.api.middleware.rate_limit import get_auth_rate_limiter

    if not request.user_id or len(request.user_id) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required"
        )

    # Check per-user auth rate limiting
    auth_limiter = get_auth_rate_limiter()
    if auth_limiter.is_rate_limited(request.user_id, action="token"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Try again in 1 hour.",
            headers={"Retry-After": "3600"},
        )

    try:
        jwt_handler = get_jwt_handler()
        token = jwt_handler.create_token(
            user_id=request.user_id,
            expires_in_hours=24
        )

        # Reset rate limit on success
        auth_limiter.reset_attempts(request.user_id, action="token")
        logger.info(f"JWT token generated for user {request.user_id}")

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=86400  # 24 hours in seconds
        )
    except Exception as e:
        # Record failed attempt for rate limiting
        auth_limiter.record_failed_attempt(request.user_id, action="token")
        logger.error(f"Failed to generate token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authentication token"
        )


@router.post("/auth/logout")
async def logout(request: Request):
    """
    Logout by revoking the current JWT token

    Requires a valid JWT token in the Authorization header.
    The token will be blacklisted and can no longer be used for authentication.

    Returns:
        Success message
    """
    token = getattr(request.state, "token", None)
    user_id = getattr(request.state, "user_id", None)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )

    try:
        from backend.api.main import get_container
        container = get_container()
        revocation_service = container.get_revocation_service()
        revocation_service.revoke_token(token)
        logger.info(f"User {user_id} logged out, token revoked")
        return {"message": "Successfully logged out", "user_id": user_id}
    except Exception as e:
        logger.error(f"Failed to process logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process logout"
        )
