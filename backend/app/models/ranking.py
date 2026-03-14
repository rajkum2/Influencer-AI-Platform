"""
Ranking and scoring models.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.influencer import Influencer
    from app.models.technology import Technology
    from app.models.user import User


class RankSnapshot(Base):
    """Historical ranking data for influencers."""
    
    __tablename__ = "rank_snapshots"
    
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
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    
    # Overall Scores
    overall_score: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 3),
        nullable=True
    )
    overall_rank: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )
    
    # Component Scores (0-100 scale)
    authority_score: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 3),
        nullable=True
    )
    relevance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 3),
        nullable=True
    )
    quality_score: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 3),
        nullable=True
    )
    engagement_score: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 3),
        nullable=True
    )
    consistency_score: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 3),
        nullable=True
    )
    growth_score: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 3),
        nullable=True
    )
    trust_score: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 3),
        nullable=True
    )
    
    # Context (null = global)
    technology_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technologies.id"),
        nullable=True,
        index=True
    )
    region: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )
    
    # Change tracking
    rank_change_7d: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rank_change_30d: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score_change_7d: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 3),
        nullable=True
    )
    score_change_30d: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 3),
        nullable=True
    )
    
    # Relationships
    influencer: Mapped["Influencer"] = relationship(
        "Influencer",
        back_populates="rank_snapshots"
    )
    technology: Mapped[Optional["Technology"]] = relationship("Technology")
    
    __table_args__ = (
        Index(
            'ix_rank_snapshots_influencer_calc',
            'influencer_id',
            'calculated_at'
        ),
        Index(
            'ix_rank_snapshots_context_rank',
            'technology_id',
            'region',
            'overall_rank'
        ),
    )
    
    def __repr__(self) -> str:
        return f"<RankSnapshot(influencer_id={self.influencer_id}, rank={self.overall_rank})>"


class RankingConfig(Base):
    """Custom ranking configurations created by users."""
    
    __tablename__ = "ranking_configs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Weights (must sum to 1.0)
    authority_weight: Mapped[float] = mapped_column(
        Numeric(3, 2),
        default=0.25
    )
    relevance_weight: Mapped[float] = mapped_column(
        Numeric(3, 2),
        default=0.20
    )
    quality_weight: Mapped[float] = mapped_column(
        Numeric(3, 2),
        default=0.20
    )
    engagement_weight: Mapped[float] = mapped_column(
        Numeric(3, 2),
        default=0.15
    )
    consistency_weight: Mapped[float] = mapped_column(
        Numeric(3, 2),
        default=0.10
    )
    growth_weight: Mapped[float] = mapped_column(
        Numeric(3, 2),
        default=0.05
    )
    trust_weight: Mapped[float] = mapped_column(
        Numeric(3, 2),
        default=0.05
    )
    
    # Filters
    technology_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technologies.id"),
        nullable=True
    )
    region_filter: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country_filter: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    platform_filter: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    role_type_filter: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Settings
    min_followers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_followers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_range_days: Mapped[int] = mapped_column(Integer, default=90)
    
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    creator: Mapped["User"] = relationship("User")
    technology: Mapped[Optional["Technology"]] = relationship("Technology")
    
    __table_args__ = (
        Index('ix_ranking_configs_creator', 'created_by'),
        Index('ix_ranking_configs_public', 'is_public'),
    )
    
    def __repr__(self) -> str:
        return f"<RankingConfig(name='{self.name}', created_by={self.created_by})>"
    
    @property
    def total_weight(self) -> float:
        """Calculate total weight (should be 1.0)."""
        return (
            self.authority_weight +
            self.relevance_weight +
            self.quality_weight +
            self.engagement_weight +
            self.consistency_weight +
            self.growth_weight +
            self.trust_weight
        )
    
    def validate_weights(self) -> bool:
        """Validate that weights sum to approximately 1.0."""
        return 0.99 <= self.total_weight <= 1.01
