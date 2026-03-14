"""
User and Team models.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.crm import InfluencerRelationship
    from app.models.influencer import Influencer
    from app.models.watchlist import Watchlist


class Team(Base):
    """Organization/team model."""
    
    __tablename__ = "teams"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    
    # Billing
    plan: Mapped[str] = mapped_column(
        String(20),
        default="free",
        index=True
    )  # free, starter, pro, enterprise
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Limits (enforced in application layer)
    max_influencers: Mapped[int] = mapped_column(Integer, default=100)
    max_team_members: Mapped[int] = mapped_column(Integer, default=3)
    max_watchlists: Mapped[int] = mapped_column(Integer, default=10)
    
    # Settings
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    
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
    members: Mapped[List["User"]] = relationship(
        "User",
        back_populates="team",
        lazy="selectin"
    )
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    watchlists: Mapped[List["Watchlist"]] = relationship(
        "Watchlist",
        back_populates="team",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name='{self.name}')>"
    
    @property
    def member_count(self) -> int:
        """Get the current number of team members."""
        return len(self.members)


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Profile
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Role
    role: Mapped[str] = mapped_column(
        String(20),
        default="member",
        index=True
    )  # superadmin, admin, member, viewer
    
    # Team
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id"),
        nullable=True
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # OAuth
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Preferences
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    notification_settings: Mapped[dict] = mapped_column(JSON, default=dict)
    
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
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="members")
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    created_influencers: Mapped[List["Influencer"]] = relationship(
        "Influencer",
        back_populates="creator",
        lazy="selectin"
    )
    influencer_relationships: Mapped[List["InfluencerRelationship"]] = relationship(
        "InfluencerRelationship",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    owned_watchlists: Mapped[List["Watchlist"]] = relationship(
        "Watchlist",
        back_populates="owner",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index('ix_users_team_role', 'team_id', 'role'),
        Index('ix_users_oauth', 'oauth_provider', 'oauth_id'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email.split("@")[0]
    
    @property
    def is_superadmin(self) -> bool:
        """Check if user is superadmin."""
        return self.role == "superadmin"
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin or higher."""
        return self.role in ("superadmin", "admin")
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_superadmin:
            return True
        # Add more granular permission checks here
        return True


class TeamMember(Base):
    """Association table for team memberships with roles."""
    
    __tablename__ = "team_members"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Role within the team
    team_role: Mapped[str] = mapped_column(
        String(20),
        default="member"
    )  # owner, admin, member
    
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="team_memberships")
    user: Mapped["User"] = relationship("User", back_populates="team_memberships")
    
    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='uq_team_member'),
        Index('ix_team_members_team_user', 'team_id', 'user_id'),
    )
