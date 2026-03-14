"""
System jobs and API usage tracking models.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SystemJob(Base):
    """Background job tracking."""
    
    __tablename__ = "system_jobs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # ingest, score, classify, sync, export, import
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True
    )  # pending, running, paused, completed, failed, cancelled
    
    # Target entity
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    # Payload
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Progress
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    items_processed: Mapped[int] = mapped_column(Integer, default=0)
    items_total: Mapped[int] = mapped_column(Integer, default=0)
    
    # Results
    result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Scheduling
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    
    # Worker info
    worker_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    queue_name: Mapped[str] = mapped_column(String(50), default="default")
    
    # Metadata
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    __table_args__ = (
        Index('ix_system_jobs_type_status', 'job_type', 'status'),
        Index('ix_system_jobs_scheduled', 'scheduled_for'),
        Index('ix_system_jobs_queue', 'queue_name', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<SystemJob(id={self.id}, type='{self.job_type}', status='{self.status}')>"
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class APIUsage(Base):
    """API usage tracking for quota management."""
    
    __tablename__ = "api_usage"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # youtube, github, twitter, etc.
    endpoint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Quota
    quota_used: Mapped[int] = mapped_column(Integer, default=1)
    quota_cost: Mapped[int] = mapped_column(Integer, default=1)
    quota_remaining: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quota_reset_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Request details
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Rate limiting
    rate_limit_remaining: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rate_limit_reset: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Context
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    __table_args__ = (
        Index('ix_api_usage_platform_date', 'platform', 'requested_at'),
        Index('ix_api_usage_account', 'account_id'),
        Index('ix_api_usage_job', 'job_id'),
    )
    
    def __repr__(self) -> str:
        return f"<APIUsage(platform='{self.platform}', endpoint='{self.endpoint}')>"
