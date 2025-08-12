"""Configuration management for Claude SDK Server."""

import os
from typing import Optional, List
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"  # Allow extra fields from environment
    )
    
    # Application settings
    app_name: str = Field(default="Claude SDK Server", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    reload: bool = Field(default=True, env="RELOAD")
    
    # Claude SDK settings
    claude_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    claude_model: str = Field(
        default="sonnet",
        env="CLAUDE_MODEL"
    )
    claude_max_tokens: int = Field(default=4096, env="CLAUDE_MAX_TOKENS")
    claude_timeout: int = Field(default=60, env="CLAUDE_TIMEOUT")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"],
        env="CORS_ALLOW_HEADERS"
    )
    
    # Redis settings
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_ttl: int = Field(default=3600, env="REDIS_TTL")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        env="LOG_FORMAT"
    )
    log_file: Optional[str] = Field(default="logs/app.log", env="LOG_FILE")
    
    # Security
    api_key_enabled: bool = Field(default=False, env="API_KEY_ENABLED")
    api_keys: List[str] = Field(default=[], env="API_KEYS")
    
    @property
    def redis_enabled(self) -> bool:
        """Check if Redis is enabled."""
        return self.redis_url is not None
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()