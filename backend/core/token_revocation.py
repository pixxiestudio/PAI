"""Token revocation service for JWT token blacklisting

Provides the ability to revoke (blacklist) JWT tokens, enabling:
- Secure logout (token immediately invalidated)
- Compromised token invalidation
- Administrative token revocation

Uses Redis as backend when available, falls back gracefully when disabled.
"""

import logging
from typing import Optional, Set
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class TokenRevocationService:
    """Service for revoking JWT tokens via Redis blacklist or in-memory fallback"""

    def __init__(self, redis_client=None):
        """
        Initialize token revocation service

        Args:
            redis_client: Redis client instance. If None, uses in-memory set as fallback.
        """
        self.redis = redis_client
        self.use_redis = redis_client is not None
        # In-memory fallback for when Redis is not available
        self._revoked_tokens: Set[str] = set()

    def revoke_token(self, token: str, expires_in: int = 86400) -> bool:
        """
        Revoke (blacklist) a JWT token

        Args:
            token: JWT token string to revoke
            expires_in: TTL in seconds (default 24 hours, matches JWT expiry)

        Returns:
            True if revocation recorded successfully
        """
        if self.use_redis:
            try:
                key = f"revoked_token:{token}"
                self.redis.setex(key, expires_in, "1")
                logger.info("Token revoked via Redis")
                return True
            except Exception as e:
                logger.error(f"Redis revocation failed, using fallback: {e}")
                self._revoked_tokens.add(token)
                return True
        else:
            self._revoked_tokens.add(token)
            logger.info("Token revoked via in-memory fallback")
            return True

    def is_revoked(self, token: str) -> bool:
        """
        Check if a JWT token has been revoked

        Args:
            token: JWT token string to check

        Returns:
            True if token is revoked
        """
        # Check in-memory first (covers fallback scenario)
        if token in self._revoked_tokens:
            return True

        if self.use_redis:
            try:
                key = f"revoked_token:{token}"
                return self.redis.exists(key) == 1
            except Exception as e:
                logger.error(f"Redis revocation check failed: {e}")
                return False

        return False

    def cleanup_memory_fallback(self, max_size: int = 10000) -> int:
        """
        Clean up in-memory fallback set to prevent unbounded growth

        Args:
            max_size: Maximum tokens to keep in memory

        Returns:
            Number of tokens removed
        """
        if len(self._revoked_tokens) <= max_size:
            return 0
        excess = len(self._revoked_tokens) - max_size
        # Remove oldest entries (sets are unordered, so we just pop)
        for _ in range(excess):
            self._revoked_tokens.pop()
        logger.info(f"Cleaned up {excess} tokens from in-memory revocation set")
        return excess
