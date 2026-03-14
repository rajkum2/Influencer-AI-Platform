"""
CRM and Relationship management models.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
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
    from app.models.user import User


class InfluencerRelationship(Base):
    """CRM relationship tracking for influencers."""
    
    __tablename__ = "influencer_relationships"
    
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
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Pipeline stage
    stage: Mapped[str] = mapped_column(
        String(50),
        default="not_contacted",
        index=True
    )  # not_contacted, contacted, responded, meeting, negotiation, partnered, declined, churned
    
    # Pipeline status details
    pipeline_value: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
    probability: Mapped[Optional[int]] = mapped_column(
        Numeric(3, 0),
        nullable=True
    )  # 0-100
    expected_close_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    actual_close_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Follow-up tracking
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    next_follow_up_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    follow_up_reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Opportunity
    opportunity_type: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )  # speaker, advisor, sponsor, podcast, content_collab, etc.
    estimated_value: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Source
    source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )  # manual, import, discovery, referral
    campaign_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    # Tags
    tags: Mapped[list] = mapped_column(JSON, default=list)
    
    # Custom fields
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    
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
    influencer: Mapped["Influencer"] = relationship(
        "Influencer",
        back_populates="relationships"
    )
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="influencer_relationships"
    )
    interactions: Mapped[List["Interaction"]] = relationship(
        "Interaction",
        back_populates="relationship",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Interaction.occurred_at)"
    )
    
    __table_args__ = (
        UniqueConstraint(
            'influencer_id',
            'owner_id',
            name='uq_influencer_owner_relationship'
        ),
        Index('ix_relationships_owner', 'owner_id'),
        Index('ix_relationships_stage', 'stage'),
        Index('ix_relationships_follow_up', 'next_follow_up_at'),
        Index('ix_relationships_owner_stage', 'owner_id', 'stage'),
    )
    
    def __repr__(self) -> str:
        return f"<InfluencerRelationship(influencer_id={self.influencer_id}, stage='{self.stage}')>"
    
    @property
    is_open(self) -> bool:
        """Check if relationship is still open/active."""
        return self.stage not in ("declined", "churned", "partnered")
    
    @property
    days_since_contact(self) -> Optional[int]:
        """Get days since last contact."""
        if not self.last_contacted_at:
            return None
        return (datetime.utcnow() - self.last_contacted_at).days
    
    @property
    days_until_follow_up(self) -> Optional[int]:
        """Get days until next follow-up."""
        if not self.next_follow_up_at:
            return None
        return (self.next_follow_up_at - datetime.utcnow()).days


class Interaction(Base):
    """Individual interactions with influencers."""
    
    __tablename__ = "interactions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    relationship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("influencer_relationships.id", ondelete="CASCADE"),
        nullable=False
    )
    
    interaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # email, dm, call, meeting, video_call, note, task
    direction: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )  # inbound, outbound
    
    # Content
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Outcome
    outcome: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )  # positive, neutral, negative, no_response
    next_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Attachments
    attachments: Mapped[list] = mapped_column(JSON, default=list)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    relationship: Mapped["InfluencerRelationship"] = relationship(
        "InfluencerRelationship",
        back_populates="interactions"
    )
    creator: Mapped["User"] = relationship("User")
    
    __table_args__ = (
        Index('ix_interactions_relationship', 'relationship_id'),
        Index('ix_interactions_type', 'interaction_type'),
        Index('ix_interactions_creator', 'created_by'),
    )
    
    def __repr__(self) -> str:
        return f"<Interaction(id={self.id}, type='{self.interaction_type}')>"
