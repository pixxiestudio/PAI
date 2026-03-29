"""JWT Authentication module for PAI API

Handles JWT token generation, validation, and verification for API security.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import jwt
import logging
from functools import lru_cache

from backend.utils.config import settings
from backend.core.exceptions import APIKeyError

logger = logging.getLogger(__name__)


class JWTHandler:
    """Handles JWT token operations for authentication"""

    def __init__(self):
        """Initialize JWT handler with secret key from config"""
        self.secret_key = settings.jwt_secret_key or "dev-secret-key-change-in-production"
        self.algorithm = "HS256"
        self.expiration_hours = 24

    def create_token(
        self,
        user_id: str,
        data: Optional[Dict[str, Any]] = None,
        expires_in_hours: Optional[int] = None
    ) -> str:
        """
        Create a JWT token for a user

        Args:
            user_id: User identifier
            data: Additional claims to include in token
            expires_in_hours: Token expiration time (defaults to 24 hours)

        Returns:
            JWT token string
        """
        if expires_in_hours is None:
            expires_in_hours = self.expiration_hours

        # Calculate expiration time
        expire = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        # Build token payload
        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        # Add additional claims
        if data:
            payload.update(data)

        # Encode token
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"JWT token created for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to create JWT token: {e}")
            raise APIKeyError(f"Failed to create authentication token: {e}")

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token

        Args:
            token: JWT token string to verify

        Returns:
            Decoded token payload

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            logger.debug(f"JWT token verified for user {payload.get('user_id')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise

    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """
        Extract user_id from token without full verification

        Args:
            token: JWT token string

        Returns:
            User ID if valid, None otherwise
        """
        try:
            payload = self.verify_token(token)
            return payload.get("user_id")
        except Exception:
            return None


# Global JWT handler instance
@lru_cache(maxsize=1)
def get_jwt_handler() -> JWTHandler:
    """Get or create JWT handler instance"""
    return JWTHandler()
