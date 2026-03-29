"""Configuration management for PAI system"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """PAI System Settings"""

    # Server Configuration
    app_name: str = "PAI - Personal AI Assistant"
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./pai.db",
        env="DATABASE_URL"
    )

    # API Keys
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")

    # Redis Configuration (for Multi-PAI network)
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )

    # Model Configuration
    default_model: str = Field(default="claude-sonnet-4-6", env="DEFAULT_MODEL")
    fast_model: str = Field(default="claude-haiku-4-5-20251001", env="FAST_MODEL")
    powerful_model: str = Field(default="claude-opus-4-6", env="POWERFUL_MODEL")

    # Local API Configuration (Ollama)
    ollama_enabled: bool = Field(default=False, env="OLLAMA_ENABLED")
    ollama_endpoint: str = Field(default="http://localhost:11434", env="OLLAMA_ENDPOINT")
    ollama_model: str = Field(default="llama2", env="OLLAMA_MODEL")

    # Token Budgets
    context_reserve_tokens: int = 3000
    response_reserve_tokens: int = 2000
    max_injection_tokens: int = 3000

    # Memory Configuration
    max_session_history: int = 10
    memory_db_path: str = Field(default="./pai_memory.db", env="MEMORY_DB_PATH")
    memory_decay_lambda: float = Field(
        default=0.1,
        env="MEMORY_DECAY_LAMBDA",
        description="Exponential decay rate for memory importance. Formula: importance = base × e^(-lambda × age_days)"
    )

    # Security
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
