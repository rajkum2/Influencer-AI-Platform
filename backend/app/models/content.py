"""
Content and Content Engagement models.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, VECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.influencer import Influencer, SocialAccount
    from app.models.technology import ContentTechnology


class ContentItem(Base):
    """Content item (video, post, article, etc.) from an influencer."""
    
    __tablename__ = "content_items"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    influencer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("influencers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    social_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_accounts.id"),
        nullable=True
    )
    
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # youtube, github, twitter, blog, etc.
    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # video, post, article, repo, podcast, etc.
    
    # Content
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    original_url: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Media
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    language_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    country_hint: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    
    # AI Enrichment
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding: Mapped[Optional[list]] = mapped_column(VECTOR(1536), nullable=True)
    
    # Quality Signals
    quality_score: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 3),
        nullable=True
    )  # 0.000 to 1.000
    spam_score: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 3),
        nullable=True
    )
    
    # Status
    processing_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True
    )  # pending, processing, completed, failed
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Engagement (cached latest values)
    views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    likes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shares: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    engagement_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    influencer: Mapped["Influencer"] = relationship(
        "Influencer",
        back_populates="content_items"
    )
    social_account: Mapped[Optional["SocialAccount"]] = relationship(
        "SocialAccount"
    )
    technologies: Mapped[List["ContentTechnology"]] = relationship(
        "ContentTechnology",
        back_populates="content_item",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    engagement_history: Mapped[List["ContentEngagement"]] = relationship(
        "ContentEngagement",
        back_populates="content_item",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(ContentEngagement.measured_at)"
    )
    
    __table_args__ = (
        Index(
            'ix_content_items_platform_external_id',
            'platform',
            'external_id',
            unique=True
        ),
        Index('ix_content_items_influencer_platform', 'influencer_id', 'platform'),
        Index('ix_content_items_published', 'published_at'),
        Index('ix_content_items_processing', 'processing_status', 'is_indexed'),
        Index(
            'ix_content_items_embedding',
            'embedding',
            postgresql_using='ivfflat'
        ),
    )
    
    def __repr__(self) -> str:
        return f"<ContentItem(id={self.id}, platform='{self.platform}', title='{self.title[:50] if self.title else None}...')>"
    
    @property
    def engagement_total(self) -> int:
        """Calculate total engagement."""
        return (
            (self.likes or 0) +
            (self.comments or 0) +
            (self.shares or 0)
        )


class ContentEngagement(Base):
    """Time-series engagement metrics for content items."""
    
    __tablename__ = "content_engagement"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    
    views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    likes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shares: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Platform specific metrics
    additional_metrics: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Relationships
    content_item: Mapped["ContentItem"] = relationship(
        "ContentItem",
        back_populates="engagement_history"
    )
    
    __table_args__ = (
        Index('ix_content_engagement_content_date', 'content_id', 'measured_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ContentEngagement(content_id={self.content_id}, measured_at={self.measured_at})>"
