"""
Anthropic API Key management via OAuth subscription
Similar to Claude Code's settings-based configuration
"""

import json
import logging
from typing import Dict, Optional, Any
from enum import Enum
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """Subscription tier levels"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class AnthropicOAuthConfig:
    """Load and manage Anthropic OAuth config (like settings.json)"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize OAuth config from JSON file

        Args:
            config_path: Path to anthropic_oauth_config.json
                        If None, uses default: backend/config/anthropic_oauth_config.json
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "anthropic_oauth_config.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.oauth_config = self.config.get("anthropic_oauth", {})

    def _load_config(self) -> Dict[str, Any]:
        """Load config from JSON file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return {}

            with open(self.config_path, 'r') as f:
                config = json.load(f)

            logger.info(f"Loaded Anthropic OAuth config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load OAuth config: {e}")
            return {}

    @property
    def is_enabled(self) -> bool:
        """Check if OAuth is enabled"""
        return self.oauth_config.get("enabled", False)

    @property
    def client_id(self) -> str:
        """Get OAuth client ID (from config or env var)"""
        env_id = os.getenv("ANTHROPIC_OAUTH_CLIENT_ID")
        if env_id:
            return env_id
        return self.oauth_config.get("oauth_config", {}).get("client_id", "")

    @property
    def client_secret(self) -> str:
        """Get OAuth client secret (from config or env var)"""
        env_secret = os.getenv("ANTHROPIC_OAUTH_CLIENT_SECRET")
        if env_secret:
            return env_secret
        return self.oauth_config.get("oauth_config", {}).get("client_secret", "")

    @property
    def redirect_uri(self) -> str:
        """Get OAuth redirect URI"""
        return self.oauth_config.get("oauth_config", {}).get("redirect_uri", "")

    @property
    def auth_url(self) -> str:
        """Get OAuth authorization URL"""
        return self.oauth_config.get("oauth_config", {}).get("auth_url", "")

    @property
    def token_url(self) -> str:
        """Get OAuth token URL"""
        return self.oauth_config.get("oauth_config", {}).get("token_url", "")

    def get_subscription_tier(self, tier_name: str) -> Dict[str, Any]:
        """
        Get subscription tier details

        Args:
            tier_name: "free", "pro", or "enterprise"

        Returns:
            Subscription tier configuration
        """
        tiers = self.oauth_config.get("subscription_tiers", {})
        return tiers.get(tier_name, tiers.get("free", {}))

    def get_tier_limits(self, tier: SubscriptionTier) -> Dict[str, Any]:
        """Get rate limits for a subscription tier"""
        tier_config = self.get_subscription_tier(tier.value)
        return {
            "monthly_requests": tier_config.get("monthly_requests"),
            "max_tokens_per_request": tier_config.get("max_tokens_per_request"),
            "concurrent_requests": tier_config.get("concurrent_requests"),
        }

    def get_features(self, tier: SubscriptionTier) -> list:
        """Get available features for a subscription tier"""
        tier_config = self.get_subscription_tier(tier.value)
        return tier_config.get("features", [])

    @property
    def api_strategy(self) -> str:
        """Get API key management strategy"""
        return self.oauth_config.get("api_key_management", {}).get("strategy", "backend_proxy")

    @property
    def billing_enabled(self) -> bool:
        """Check if billing is enabled"""
        return self.oauth_config.get("billing", {}).get("enabled", False)

    @property
    def billing_provider(self) -> str:
        """Get billing provider (stripe, etc)"""
        return self.oauth_config.get("billing", {}).get("provider", "stripe")

    def update_config(self, updates: Dict[str, Any]):
        """
        Update config in memory (like editing settings.json)

        Args:
            updates: Dictionary with config changes
        """
        self.oauth_config.update(updates)
        logger.info(f"Updated OAuth config: {list(updates.keys())}")

    def save_config(self):
        """Save current config back to JSON file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved OAuth config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save OAuth config: {e}")

    def __repr__(self) -> str:
        return f"<AnthropicOAuthConfig enabled={self.is_enabled} strategy={self.api_strategy}>"


class AnthropicOAuthService:
    """Service to handle OAuth authentication and API key access"""

    def __init__(self, config: AnthropicOAuthConfig):
        """
        Initialize OAuth service

        Args:
            config: AnthropicOAuthConfig instance
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def authenticate_user(self, auth_code: str) -> Dict[str, Any]:
        """
        Exchange OAuth code for tokens

        Args:
            auth_code: Authorization code from OAuth callback

        Returns:
            User info and tokens
        """
        if not self.config.is_enabled:
            raise ValueError("OAuth not enabled")

        # TODO: Implement OAuth token exchange
        # This would call the Anthropic OAuth token endpoint
        # and return access_token, refresh_token, user_id, etc.

        self.logger.info(f"Authenticating user with code: {auth_code[:20]}...")

        return {
            "access_token": "token_...",
            "refresh_token": "refresh_...",
            "user_id": "user_...",
            "expires_in": 3600,
            "scope": self.config.oauth_config.get("oauth_config", {}).get("scope", [])
        }

    async def get_user_api_key(self, user_id: str) -> Optional[str]:
        """
        Get or create API key for user

        Args:
            user_id: User ID

        Returns:
            API key for the user (temporary or permanent based on strategy)
        """
        strategy = self.config.api_strategy

        if strategy == "backend_proxy":
            # Return backend's master key (request will be proxied)
            return os.getenv("ANTHROPIC_API_KEY")

        elif strategy == "user_temporary_keys":
            # TODO: Create temporary API key for user
            pass

        elif strategy == "hybrid":
            # TODO: Check subscription tier, decide strategy
            pass

        return None

    async def check_rate_limit(self, user_id: str, tier: SubscriptionTier) -> Dict[str, Any]:
        """
        Check if user is within rate limits

        Args:
            user_id: User ID
            tier: Subscription tier

        Returns:
            Rate limit status
        """
        limits = self.config.get_tier_limits(tier)

        # TODO: Query database for user's current usage
        # Compare against limits

        return {
            "allowed": True,
            "remaining_requests": limits["monthly_requests"],
            "reset_at": "2026-04-30T00:00:00Z"
        }

    async def track_usage(self, user_id: str, tokens_used: int, cost: float):
        """
        Track API usage for a user

        Args:
            user_id: User ID
            tokens_used: Number of tokens used
            cost: Cost in dollars
        """
        # TODO: Record usage in database
        self.logger.info(f"User {user_id}: {tokens_used} tokens, ${cost:.2f}")

    async def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get subscription status for user

        Args:
            user_id: User ID

        Returns:
            Subscription details
        """
        # TODO: Query database for subscription info
        return {
            "user_id": user_id,
            "tier": SubscriptionTier.FREE.value,
            "status": "active",
            "billing_cycle_start": "2026-03-01",
            "billing_cycle_end": "2026-04-01",
            "usage_this_month": {
                "requests": 250,
                "tokens": 125000
            }
        }


# Global config instance (like Claude Code's settings)
_oauth_config: Optional[AnthropicOAuthConfig] = None


def get_oauth_config() -> AnthropicOAuthConfig:
    """
    Get global OAuth config (lazy load)
    Similar to how Claude Code loads settings.json
    """
    global _oauth_config

    if _oauth_config is None:
        _oauth_config = AnthropicOAuthConfig()

    return _oauth_config


def get_oauth_service() -> AnthropicOAuthService:
    """Get OAuth service instance"""
    config = get_oauth_config()
    return AnthropicOAuthService(config)
