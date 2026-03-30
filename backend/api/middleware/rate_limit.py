"""Rate Limiting Middleware for FastAPI

Implements token bucket rate limiting to prevent API abuse,
plus per-user authentication rate limiting to prevent account enumeration.
"""

import logging
import time
from typing import Dict, Tuple, Optional
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from functools import lru_cache

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limiting configuration"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        """
        Initialize rate limit configuration

        Args:
            requests_per_minute: Max requests per minute per user
            requests_per_hour: Max requests per hour per user
            burst_size: Max burst request size
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size


class RateLimiter:
    """Token bucket rate limiter implementation"""

    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter

        Args:
            config: RateLimitConfig instance
        """
        self.config = config
        # Store: {user_id: (minute_tokens, minute_reset_time, hour_tokens, hour_reset_time)}
        self.buckets: Dict[str, Tuple[float, float, float, float]] = {}

    def is_allowed(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if request is allowed under rate limits

        Args:
            user_id: User identifier

        Returns:
            Tuple of (is_allowed: bool, error_message: Optional[str])
        """
        now = time.time()
        minute_window = 60  # 1 minute
        hour_window = 3600  # 1 hour

        # Get or initialize bucket
        if user_id not in self.buckets:
            self.buckets[user_id] = (
                self.config.requests_per_minute,  # minute tokens
                now,  # minute reset time
                self.config.requests_per_hour,  # hour tokens
                now,  # hour reset time
            )

        minute_tokens, minute_reset, hour_tokens, hour_reset = self.buckets[user_id]

        # Refill minute bucket if window has passed
        if now - minute_reset >= minute_window:
            minute_tokens = self.config.requests_per_minute
            minute_reset = now

        # Refill hour bucket if window has passed
        if now - hour_reset >= hour_window:
            hour_tokens = self.config.requests_per_hour
            hour_reset = now

        # Check rate limits
        if minute_tokens <= 0:
            retry_after = int(minute_window - (now - minute_reset))
            return False, f"Rate limit exceeded (per minute). Retry after {retry_after}s"

        if hour_tokens <= 0:
            retry_after = int(hour_window - (now - hour_reset))
            return False, f"Rate limit exceeded (per hour). Retry after {retry_after}s"

        # Consume tokens
        minute_tokens -= 1
        hour_tokens -= 1

        # Update bucket
        self.buckets[user_id] = (
            minute_tokens,
            minute_reset,
            hour_tokens,
            hour_reset,
        )

        return True, None

    def cleanup_old_buckets(self, threshold_seconds: int = 3600):
        """
        Remove old buckets to prevent memory leak

        Args:
            threshold_seconds: Remove buckets inactive for this long
        """
        now = time.time()
        expired = [
            user_id
            for user_id, (_, minute_reset, _, hour_reset) in self.buckets.items()
            if now - minute_reset > threshold_seconds
            and now - hour_reset > threshold_seconds
        ]

        for user_id in expired:
            del self.buckets[user_id]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired rate limit buckets")


class AuthRateLimiter:
    """Per-user authentication rate limiter to prevent account enumeration"""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 3600):
        """
        Initialize auth rate limiter

        Args:
            max_attempts: Maximum failed auth attempts per user per window
            window_seconds: Time window in seconds (default 1 hour)
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        # Format: {identifier: [(timestamp, action), ...]}
        self._attempts: Dict[str, list] = {}

    def record_failed_attempt(self, identifier: str, action: str = "login") -> None:
        """Record a failed authentication attempt"""
        now = time.time()
        if identifier not in self._attempts:
            self._attempts[identifier] = []
        self._attempts[identifier].append((now, action))
        logger.warning(f"Failed {action} attempt for {identifier}")

    def is_rate_limited(self, identifier: str, action: str = "login") -> bool:
        """Check if identifier is rate limited for the given action"""
        if identifier not in self._attempts:
            return False

        now = time.time()
        window_start = now - self.window_seconds

        # Remove old attempts outside window
        self._attempts[identifier] = [
            (ts, act) for ts, act in self._attempts[identifier]
            if ts > window_start and act == action
        ]

        if len(self._attempts[identifier]) >= self.max_attempts:
            logger.warning(f"Auth rate limit reached for {identifier} ({action})")
            return True

        return False

    def reset_attempts(self, identifier: str, action: str = "login") -> None:
        """Reset rate limit on successful authentication"""
        if identifier in self._attempts:
            self._attempts[identifier] = [
                (ts, act) for ts, act in self._attempts[identifier]
                if act != action
            ]

    def cleanup(self, threshold_seconds: int = 7200) -> int:
        """Remove stale entries to prevent memory growth"""
        now = time.time()
        removed = 0
        expired_keys = [
            key for key, attempts in self._attempts.items()
            if not attempts or all(now - ts > threshold_seconds for ts, _ in attempts)
        ]
        for key in expired_keys:
            del self._attempts[key]
            removed += 1
        return removed


# Global rate limiter instance
@lru_cache(maxsize=1)
def get_auth_rate_limiter() -> AuthRateLimiter:
    """Get or create auth rate limiter instance"""
    return AuthRateLimiter(max_attempts=5, window_seconds=3600)


# Global rate limiter instance
@lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance"""
    config = RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        burst_size=10
    )
    return RateLimiter(config)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting

    Uses user_id from JWT token (set by auth middleware) or IP address as fallback.
    """

    # Endpoints exempt from rate limiting
    EXEMPT_ENDPOINTS = {
        "/health",
        "/metrics",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next):
        """
        Process request and apply rate limiting

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler

        Returns:
            Response if allowed, 429 Too Many Requests if rate limited
        """
        # Skip rate limiting for exempt endpoints
        if self._is_exempt(request.url.path):
            return await call_next(request)

        # Get user identifier
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            # Fallback to IP address if no user_id (public endpoint)
            user_id = request.client.host if request.client else "unknown"

        # Check rate limit
        rate_limiter = get_rate_limiter()
        is_allowed, error_message = rate_limiter.is_allowed(user_id)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user {user_id}: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_message,
                headers={"Retry-After": "60"},
            )

        # Periodically clean up old buckets
        if len(rate_limiter.buckets) % 100 == 0:
            rate_limiter.cleanup_old_buckets()

        # Call next middleware/handler
        response = await call_next(request)
        return response

    def _is_exempt(self, path: str) -> bool:
        """
        Check if endpoint is exempt from rate limiting

        Args:
            path: Request path

        Returns:
            True if endpoint is exempt, False otherwise
        """
        return path in self.EXEMPT_ENDPOINTS or path.startswith("/api/v1/health")
