"""
OAuth subscription endpoints for API key access
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from backend.core.anthropic_oauth_service import get_oauth_service, get_oauth_config, SubscriptionTier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/oauth", tags=["oauth"])


# Request/Response Models
class OAuthCallbackRequest(BaseModel):
    """OAuth authorization callback"""
    code: str
    state: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    """OAuth token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    subscription_tier: str


class SubscriptionStatusResponse(BaseModel):
    """Subscription status response"""
    user_id: str
    tier: str
    status: str
    billing_cycle_start: str
    billing_cycle_end: str
    usage_this_month: Dict[str, int]
    limits: Dict[str, Any]
    features: list


class RateLimitResponse(BaseModel):
    """Rate limit check response"""
    allowed: bool
    remaining_requests: int
    reset_at: str


# Endpoints
@router.get("/login")
async def oauth_login_url():
    """
    Get OAuth login URL for user

    Returns:
        URL to redirect user to Anthropic OAuth
    """
    config = get_oauth_config()

    if not config.is_enabled:
        raise HTTPException(status_code=400, detail="OAuth not enabled")

    auth_url = config.auth_url
    client_id = config.client_id
    redirect_uri = config.redirect_uri
    scope = "+".join(config.oauth_config.get("oauth_config", {}).get("scope", []))

    full_url = f"{auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type=code"

    return {"login_url": full_url}


@router.post("/callback")
async def oauth_callback(request: OAuthCallbackRequest) -> OAuthTokenResponse:
    """
    Handle OAuth callback after user authorizes

    Args:
        request: OAuth authorization code

    Returns:
        Access token and user info
    """
    service = get_oauth_service()
    config = get_oauth_config()

    if not config.is_enabled:
        raise HTTPException(status_code=400, detail="OAuth not enabled")

    try:
        # Exchange code for tokens
        auth_result = await service.authenticate_user(request.code)

        user_id = auth_result.get("user_id")
        access_token = auth_result.get("access_token")

        # Get subscription status
        sub_status = await service.get_subscription_status(user_id)

        logger.info(f"User {user_id} authenticated via OAuth")

        return OAuthTokenResponse(
            access_token=access_token,
            expires_in=auth_result.get("expires_in", 3600),
            user_id=user_id,
            subscription_tier=sub_status.get("tier", "free")
        )

    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")


@router.get("/subscription/{user_id}")
async def get_subscription(user_id: str) -> SubscriptionStatusResponse:
    """
    Get subscription status for user

    Args:
        user_id: User ID

    Returns:
        Subscription details and limits
    """
    service = get_oauth_service()
    config = get_oauth_config()

    try:
        sub_status = await service.get_subscription_status(user_id)

        tier = SubscriptionTier(sub_status.get("tier", "free"))
        limits = config.get_tier_limits(tier)
        features = config.get_features(tier)

        return SubscriptionStatusResponse(
            user_id=user_id,
            tier=tier.value,
            status=sub_status.get("status"),
            billing_cycle_start=sub_status.get("billing_cycle_start"),
            billing_cycle_end=sub_status.get("billing_cycle_end"),
            usage_this_month=sub_status.get("usage_this_month", {}),
            limits=limits,
            features=features
        )

    except Exception as e:
        logger.error(f"Failed to get subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription")


@router.get("/rate-limit/{user_id}")
async def check_rate_limit(user_id: str) -> RateLimitResponse:
    """
    Check if user is within rate limits

    Args:
        user_id: User ID

    Returns:
        Rate limit status
    """
    service = get_oauth_service()

    try:
        sub_status = await service.get_subscription_status(user_id)
        tier = SubscriptionTier(sub_status.get("tier", "free"))

        rate_limit = await service.check_rate_limit(user_id, tier)

        return RateLimitResponse(
            allowed=rate_limit.get("allowed", True),
            remaining_requests=rate_limit.get("remaining_requests", 0),
            reset_at=rate_limit.get("reset_at", "")
        )

    except Exception as e:
        logger.error(f"Failed to check rate limit: {e}")
        raise HTTPException(status_code=500, detail="Failed to check rate limit")


@router.get("/config")
async def get_oauth_config_info():
    """
    Get OAuth configuration info (for debugging/setup)

    Returns:
        OAuth config details
    """
    config = get_oauth_config()

    return {
        "enabled": config.is_enabled,
        "provider": config.oauth_config.get("provider"),
        "strategy": config.api_strategy,
        "tiers": list(config.oauth_config.get("subscription_tiers", {}).keys()),
        "billing_enabled": config.billing_enabled,
        "security": {
            "encrypt_api_keys": config.oauth_config.get("security", {}).get("encrypt_api_keys"),
            "require_https": config.oauth_config.get("security", {}).get("require_https")
        }
    }


@router.get("/tiers")
async def list_subscription_tiers():
    """
    Get all available subscription tiers

    Returns:
        Tier information
    """
    config = get_oauth_config()

    tiers = {}
    for tier_name, tier_config in config.oauth_config.get("subscription_tiers", {}).items():
        tiers[tier_name] = {
            "name": tier_config.get("name"),
            "monthly_requests": tier_config.get("monthly_requests"),
            "max_tokens_per_request": tier_config.get("max_tokens_per_request"),
            "concurrent_requests": tier_config.get("concurrent_requests"),
            "features": tier_config.get("features", []),
            "cost": tier_config.get("cost")
        }

    return {"tiers": tiers}
