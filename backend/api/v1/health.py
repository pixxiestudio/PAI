"""Health check and monitoring endpoints"""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone

from backend.api.main import get_container
from backend.core.container import ServiceContainer
from backend.core.models import HealthCheck

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check(container: ServiceContainer = Depends(get_container)):
    """
    Health check endpoint for monitoring

    Returns:
        HealthCheck status
    """
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="2.0.0"
    )


@router.get("/metrics")
async def get_metrics(container: ServiceContainer = Depends(get_container)):
    """
    Get system metrics for monitoring

    Returns:
        Metrics including session count, uptime, etc.
    """
    engine = container.get_engine()

    return {
        "timestamp": datetime.now(timezone.utc),
        "active_sessions": len(engine.sessions),
        "api_version": "2.0.0",
        "status": "operational"
    }


@router.get("/ready")
async def readiness_check(container: ServiceContainer = Depends(get_container)):
    """
    Readiness probe for Kubernetes/Docker

    Returns:
        Status indicating if service is ready to accept traffic
    """
    return {
        "ready": True,
        "timestamp": datetime.now(timezone.utc)
    }
