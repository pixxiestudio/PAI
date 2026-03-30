"""Dependency Injection Container for PAI

This module provides the ServiceContainer class which manages
the lifecycle and dependency injection of all PAI services.

This container is used by Phase 2+ to wire services together without
relying on global singletons.

Usage:
    # Create container
    from backend.utils.config import settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_engine = create_engine(settings.database_url)
    db_session_factory = sessionmaker(bind=db_engine)
    db_session = db_session_factory()

    container = ServiceContainer(db_session=db_session)

    # Use services
    engine = container.get_engine()
    memory = container.get_memory_system()
    learning = container.get_learning_system()

    # In FastAPI:
    @app.get("/chat/{session_id}")
    async def chat(session_id: str,
                   container: ServiceContainer = Depends(get_container)):
        engine = container.get_engine()
        return await engine.send_message(session_id, "hello")
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session as DBSession

from backend.utils.config import Settings, settings
from backend.core.engine import PAIEngine
from backend.core.memory import MemorySystem
from backend.core.context import ContextManager
from backend.core.learning import SelfLearningSystem
from backend.core.personality import PersonalityManager
from backend.core.token_revocation import TokenRevocationService
from backend.integrations.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Dependency Injection Container for PAI services

    Manages the lifecycle of all service instances and provides
    lazy initialization to avoid unnecessary resource allocation.

    This container is the single source of truth for service instances
    within an application context (e.g., a FastAPI request).

    Example:
        container = ServiceContainer(db_session=db_session)
        engine = container.get_engine()
        memory = container.get_memory_system()
    """

    def __init__(self, db_session: Optional[DBSession] = None,
                 config: Optional[Settings] = None):
        """
        Initialize the service container

        Args:
            db_session: SQLAlchemy database session for persistence
                       If None, services operate in-memory (no persistence)
            config: Configuration object (uses global settings if not provided)
        """
        self.db_session = db_session
        self.config = config or settings

        # Lazy-initialized services
        self._engine: Optional[PAIEngine] = None
        self._memory_system: Optional[MemorySystem] = None
        self._context_manager: Optional[ContextManager] = None
        self._learning_system: Optional[SelfLearningSystem] = None
        self._personality_manager: Optional[PersonalityManager] = None
        self._skill_registry: Optional[SkillRegistry] = None

        # Initialize token revocation (eager - needed for auth middleware)
        self._redis_client = None
        self._revocation_service = self._init_revocation_service()

        logger.debug(
            f"ServiceContainer initialized with "
            f"db_session={db_session is not None}, "
            f"config={self.config.app_name}"
        )

    def _init_revocation_service(self) -> TokenRevocationService:
        """Initialize token revocation service with Redis or in-memory fallback"""
        if self.config.redis_enabled:
            try:
                import redis
                self._redis_client = redis.from_url(
                    self.config.redis_url,
                    decode_responses=True
                )
                self._redis_client.ping()
                logger.info("Redis connected - token revocation via Redis")
                return TokenRevocationService(redis_client=self._redis_client)
            except Exception as e:
                logger.warning(f"Redis unavailable ({e}), using in-memory token revocation")
                return TokenRevocationService(redis_client=None)
        else:
            logger.info("Redis disabled - using in-memory token revocation")
            return TokenRevocationService(redis_client=None)

    def get_engine(self) -> PAIEngine:
        """
        Get or create PAIEngine instance

        Returns:
            PAIEngine configured with this container's database session
        """
        if self._engine is None:
            logger.debug("Initializing PAIEngine")
            self._engine = PAIEngine(db_session=self.db_session)
        return self._engine

    def get_memory_system(self) -> MemorySystem:
        """
        Get or create MemorySystem instance

        Returns:
            MemorySystem configured with this container's database session
        """
        if self._memory_system is None:
            logger.debug("Initializing MemorySystem")
            self._memory_system = MemorySystem(
                db_session=self.db_session,
                memory_decay_lambda=self.config.memory_decay_lambda
            )
        return self._memory_system

    def get_context_manager(self) -> ContextManager:
        """
        Get or create ContextManager instance

        Returns:
            ContextManager with memory system and database session configured
        """
        if self._context_manager is None:
            logger.debug("Initializing ContextManager")
            memory_system = self.get_memory_system()
            self._context_manager = ContextManager(
                memory_system=memory_system,
                db_session=self.db_session
            )
        return self._context_manager

    def get_learning_system(self) -> SelfLearningSystem:
        """
        Get or create SelfLearningSystem instance

        Returns:
            SelfLearningSystem configured with this container's database session
        """
        if self._learning_system is None:
            logger.debug("Initializing SelfLearningSystem")
            self._learning_system = SelfLearningSystem(db_session=self.db_session)
        return self._learning_system

    def get_personality_manager(self) -> PersonalityManager:
        """
        Get or create PersonalityManager instance

        Returns:
            PersonalityManager configured with this container's database session
        """
        if self._personality_manager is None:
            logger.debug("Initializing PersonalityManager")
            self._personality_manager = PersonalityManager(db_session=self.db_session)
        return self._personality_manager

    def get_revocation_service(self) -> TokenRevocationService:
        """
        Get the token revocation service

        Returns:
            TokenRevocationService instance (always available, uses fallback if no Redis)
        """
        return self._revocation_service

    def get_skill_registry(self) -> SkillRegistry:
        """
        Get or create SkillRegistry instance

        Returns:
            SkillRegistry for skill management and execution
        """
        if self._skill_registry is None:
            logger.debug("Initializing SkillRegistry")
            self._skill_registry = SkillRegistry(db_session=self.db_session)
        return self._skill_registry

    def get_all_services(self) -> dict:
        """
        Get dictionary of all service instances

        Useful for debugging or monitoring service initialization state.

        Returns:
            Dict with service names and instances
        """
        return {
            "engine": self._engine,
            "memory_system": self._memory_system,
            "context_manager": self._context_manager,
            "learning_system": self._learning_system,
            "personality_manager": self._personality_manager,
            "skill_registry": self._skill_registry,
        }

    def reset(self) -> None:
        """
        Reset all services to uninitialized state

        Useful for testing or when needing to reinitialize services.
        """
        logger.warning("Resetting ServiceContainer - clearing all service instances")
        self._engine = None
        self._memory_system = None
        self._context_manager = None
        self._learning_system = None
        self._personality_manager = None
        self._skill_registry = None

    async def shutdown(self) -> None:
        """
        Clean up resources when container is shutting down

        This should be called during application shutdown to ensure
        proper cleanup of services.
        """
        logger.info("ServiceContainer shutting down")

        # Cleanup services in reverse order of dependencies
        if self._skill_registry:
            # Skills may have cleanup methods
            for skill_name in list(self._skill_registry.loaded_skills.keys()):
                await self._skill_registry.unregister(skill_name)

        # Close Redis connection if present
        if self._redis_client:
            try:
                self._redis_client.close()
                logger.debug("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

        # Close database session if present
        if self.db_session:
            try:
                self.db_session.close()
                logger.debug("Database session closed")
            except Exception as e:
                logger.error(f"Error closing database session: {e}")

        logger.info("ServiceContainer shutdown complete")


# Global container instance (for backward compatibility with Phase 1)
_container: Optional[ServiceContainer] = None


def get_container(db_session: Optional[DBSession] = None,
                  config: Optional[Settings] = None) -> ServiceContainer:
    """
    Get or create the global service container

    This function provides backward compatibility with Phase 1 code
    while supporting Phase 2's DI patterns.

    For Phase 2 FastAPI integration, use this as a dependency:
        @app.get("/chat")
        async def chat(container: ServiceContainer = Depends(get_container)):
            engine = container.get_engine()

    Args:
        db_session: Database session (uses global if not provided)
        config: Configuration (uses global if not provided)

    Returns:
        ServiceContainer instance
    """
    global _container

    if _container is None:
        _container = ServiceContainer(db_session=db_session, config=config)

    return _container


def reset_container() -> None:
    """
    Reset the global service container

    Useful for testing or when needing to reinitialize services.
    """
    global _container
    if _container:
        _container.reset()
