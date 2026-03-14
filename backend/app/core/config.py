"""
Application configuration management.
Uses Pydantic Settings for environment variable validation and type safety.
"""

import secrets
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ==========================================
    # Application
    # ==========================================
    app_name: str = "AI Influencer Discovery Platform"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # ==========================================
    # Security
    # ==========================================
    secret_key: str = secrets.token_urlsafe(32)
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # ==========================================
    # Database
    # ==========================================
    database_url: PostgresDsn = "postgresql+asyncpg://platform:platform@localhost:5432/influencer_platform"
    sync_database_url: PostgresDsn = "postgresql://platform:platform@localhost:5432/influencer_platform"
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_echo: bool = False
    
    # ==========================================
    # Redis
    # ==========================================
    redis_url: RedisDsn = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    
    # ==========================================
    # Search (Meilisearch)
    # ==========================================
    meilisearch_url: str = "http://localhost:7700"
    meilisearch_api_key: Optional[str] = None
    meilisearch_timeout: int = 30
    
    # ==========================================
    # Vector Database (Qdrant)
    # ==========================================
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = "content_embeddings"
    qdrant_vector_size: int = 1536  # OpenAI ada-002
    
    # ==========================================
    # Analytics (ClickHouse)
    # ==========================================
    clickhouse_url: str = "http://localhost:8123"
    clickhouse_user: str = "default"
    clickhouse_password: Optional[str] = None
    clickhouse_database: str = "analytics"
    
    # ==========================================
    # Storage (S3/MinIO)
    # ==========================================
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "influencer-platform"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False
    s3_url_expiration: int = 3600  # 1 hour
    
    # ==========================================
    # AI Services
    # ==========================================
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-ada-002"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-haiku-20240307"
    
    # ==========================================
    # Platform APIs
    # ==========================================
    youtube_api_key: Optional[str] = None
    youtube_quota_daily: int = 10000
    github_token: Optional[str] = None
    twitter_bearer_token: Optional[str] = None
    bluesky_handle: Optional[str] = None
    bluesky_password: Optional[str] = None
    
    # ==========================================
    # Email
    # ==========================================
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: bool = True
    email_from: str = "noreply@influencer-platform.com"
    email_enabled: bool = False
    
    # ==========================================
    # Celery
    # ==========================================
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_serializer: str = "json"
    celery_accept_content: List[str] = ["json"]
    celery_result_serializer: str = "json"
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True
    celery_task_track_started: bool = True
    celery_task_time_limit: int = 3600  # 1 hour
    celery_worker_prefetch_multiplier: int = 1
    
    # ==========================================
    # Feature Flags
    # ==========================================
    enable_ai_classification: bool = True
    enable_auto_sync: bool = True
    enable_notifications: bool = True
    enable_public_api: bool = False
    
    # ==========================================
    # Rate Limiting
    # ==========================================
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # ==========================================
    # Pagination
    # ==========================================
    default_page_size: int = 20
    max_page_size: int = 100
    
    # ==========================================
    # Content Processing
    # ==========================================
    max_content_length: int = 50000  # characters
    summary_max_length: int = 500
    embedding_batch_size: int = 100
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment.lower() == "testing"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
