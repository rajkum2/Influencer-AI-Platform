"""
Watchlist and saved lists models.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
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
    from app.models.user import Team, User


class Watchlist(Base):
    """User-created lists of influencers."""
    
    __tablename__ = "watchlists"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id"),
        nullable=True
    )
    
    # Sharing
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    shared_with: Mapped[list] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        default=list
    )
    share_permission: Mapped[str] = mapped_column(
        String(20),
        default="view"
    )  # view, edit, admin
    
    # Dynamic list filters (for smart lists)
    filter_criteria: Mapped[dict] = mapped_column(JSON, default=dict)
    is_dynamic: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Alerts
    alert_config: Mapped[dict] = mapped_column(JSON, default=dict)
    # Example:
    # {
    #   "new_content": true,
    #   "rank_change": {"enabled": true, "threshold": 10},
    #   "follower_milestone": {"enabled": true, "threshold": 10000}
    # }
    
    # Display
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
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
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_watchlists"
    )
    team: Mapped[Optional["Team"]] = relationship(
        "Team",
        back_populates="watchlists"
    )
    members: Mapped[List["WatchlistMember"]] = relationship(
        "WatchlistMember",
        back_populates="watchlist",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index('ix_watchlists_owner', 'owner_id'),
        Index('ix_watchlists_team', 'team_id'),
        Index('ix_watchlists_shared', 'is_shared'),
    )
    
    def __repr__(self) -> str:
        return f"<Watchlist(id={self.id}, name='{self.name}')>"
    
    @property
    def member_count(self) -> int:
        """Get number of influencers in watchlist."""
        return len(self.members)
    
    @property
    is_personal(self) -> bool:
        """Check if this is a personal watchlist."""
        return self.team_id is None


class WatchlistMember(Base):
    """Association between watchlists and influencers."""
    
    __tablename__ = "watchlist_members"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watchlists.id", ondelete="CASCADE"),
        nullable=False
    )
    influencer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("influencers.id", ondelete="CASCADE"),
        nullable=False
    )
    
    added_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # User notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    
    # Relationships
    watchlist: Mapped["Watchlist"] = relationship(
        "Watchlist",
        back_populates="members"
    )
    influencer: Mapped["Influencer"] = relationship(
        "Influencer",
        back_populates="watchlist_memberships"
    )
    added_by_user: Mapped[Optional["User"]] = relationship("User")
    
    __table_args__ = (
        UniqueConstraint(
            'watchlist_id',
            'influencer_id',
            name='uq_watchlist_influencer'
        ),
        Index('ix_watchlist_members_watchlist', 'watchlist_id'),
        Index('ix_watchlist_members_influencer', 'influencer_id'),
    )
