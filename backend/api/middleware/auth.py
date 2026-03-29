"""JWT Authentication Middleware for FastAPI

Validates JWT tokens in Authorization headers and injects user context.
"""

import logging
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import jwt

from backend.core.auth import get_jwt_handler

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate JWT tokens in Authorization headers

    Public endpoints (health, ready) bypass authentication.
    Protected endpoints require valid JWT token.
    """

    # Endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/health",
        "/metrics",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Callable:
        """
        Process request and validate JWT token if required

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler

        Returns:
            Response with user context injected if authenticated
        """
        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        # Extract and validate token
        token = self._extract_token(request)

        if not token:
            logger.warning(f"Missing authentication token for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token
        try:
            jwt_handler = get_jwt_handler()
            payload = jwt_handler.verify_token(token)
            user_id = payload.get("user_id")

            # Inject user_id into request state
            request.state.user_id = user_id
            logger.debug(f"Authenticated user {user_id} for {request.url.path}")

        except jwt.ExpiredSignatureError:
            logger.warning("Expired token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Call next middleware/handler
        response = await call_next(request)
        return response

    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header

        Args:
            request: FastAPI request object

        Returns:
            Token string if present, None otherwise
        """
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        # Expected format: "Bearer <token>"
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if endpoint is public (doesn't require authentication)

        Args:
            path: Request path

        Returns:
            True if endpoint is public, False otherwise
        """
        return path in self.PUBLIC_ENDPOINTS or path.startswith("/api/v1/health")


async def get_current_user(request: Request) -> str:
    """
    Dependency to get current authenticated user

    Args:
        request: FastAPI request object

    Returns:
        User ID from JWT token

    Raises:
        HTTPException: If user not authenticated
    """
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return user_id
