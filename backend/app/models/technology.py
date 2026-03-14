"""
Technology/Topic taxonomy models.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    ARRAY,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, VECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.content import ContentItem
    from app.models.influencer import Influencer


class Technology(Base):
    """Technology/topic taxonomy model."""
    
    __tablename__ = "technologies"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Hierarchy
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technologies.id"),
        nullable=True
    )
    
    # For AI classification
    keywords: Mapped[Optional[list]] = mapped_column(
        ARRAY(String),
        default=list
    )
    embedding: Mapped[Optional[list]] = mapped_column(VECTOR(1536), nullable=True)
    
    # Stats (denormalized for performance)
    influencer_count: Mapped[int] = mapped_column(Integer, default=0)
    content_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Display
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    parent: Mapped[Optional["Technology"]] = relationship(
        "Technology",
        remote_side=[id],
        back_populates="children"
    )
    children: Mapped[List["Technology"]] = relationship(
        "Technology",
        back_populates="parent",
        lazy="selectin"
    )
    influencer_mappings: Mapped[List["InfluencerTechnology"]] = relationship(
        "InfluencerTechnology",
        back_populates="technology",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    content_mappings: Mapped[List["ContentTechnology"]] = relationship(
        "ContentTechnology",
        back_populates="technology",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index(
            'ix_technologies_embedding',
            'embedding',
            postgresql_using='ivfflat'
        ),
        Index('ix_technologies_active_order', 'is_active', 'display_order'),
    )
    
    def __repr__(self) -> str:
        return f"<Technology(id={self.id}, name='{self.name}')>"
    
    @property
    def full_path(self) -> str:
        """Get full path of technology (e.g., 'AI > LLMs > Fine-tuning')."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class InfluencerTechnology(Base):
    """Association between influencers and technologies."""
    
    __tablename__ = "influencer_technologies"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    influencer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("influencers.id", ondelete="CASCADE"),
        nullable=False
    )
    technology_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technologies.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Scoring
    relevance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 3),
        nullable=True
    )
    content_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Source
    detection_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )  # ai_classified, manual, self_reported
    confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 3),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    influencer: Mapped["Influencer"] = relationship(
        "Influencer",
        back_populates="technologies"
    )
    technology: Mapped["Technology"] = relationship(
        "Technology",
        back_populates="influencer_mappings"
    )
    
    __table_args__ = (
        UniqueConstraint(
            'influencer_id',
            'technology_id',
            name='uq_influencer_technology'
        ),
        Index('ix_influencer_tech_influencer', 'influencer_id'),
        Index('ix_influencer_tech_technology', 'technology_id'),
        Index(
            'ix_influencer_tech_relevance',
            'influencer_id',
            'relevance_score'
        ),
    )


class ContentTechnology(Base):
    """Association between content items and technologies."""
    
    __tablename__ = "content_technologies"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False
    )
    technology_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technologies.id", ondelete="CASCADE"),
        nullable=False
    )
    
    relevance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 3),
        nullable=True
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 3),
        nullable=True
    )
    detection_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    
    # Relationships
    content_item: Mapped["ContentItem"] = relationship(
        "ContentItem",
        back_populates="technologies"
    )
    technology: Mapped["Technology"] = relationship(
        "Technology",
        back_populates="content_mappings"
    )
    
    __table_args__ = (
        UniqueConstraint(
            'content_id',
            'technology_id',
            name='uq_content_technology'
        ),
        Index('ix_content_tech_content', 'content_id'),
        Index('ix_content_tech_technology', 'technology_id'),
    )
