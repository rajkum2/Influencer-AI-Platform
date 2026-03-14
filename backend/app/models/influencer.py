"""
Influencer and Social Account models.
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
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.content import ContentItem
    from app.models.crm import InfluencerRelationship
    from app.models.ranking import RankSnapshot
    from app.models.technology import InfluencerTechnology
    from app.models.user import User
    from app.models.watchlist import WatchlistMember


class Influencer(Base):
    """Main influencer profile model."""
    
    __tablename__ = "influencers"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    headline: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Location
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Professional
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role_type: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True,
        index=True
    )  # founder, researcher, educator, engineer, investor, indie
    
    # Contact
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    email_public: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Media
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    profile_image_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    verification_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True
    )  # pending, verified, rejected
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Full-text search
    search_vector: Mapped[Optional[str]] = mapped_column(TSVECTOR, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Computed fields (updated by triggers or background jobs)
    total_followers: Mapped[int] = mapped_column(Integer, default=0)
    content_count: Mapped[int] = mapped_column(Integer, default=0)
    last_content_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    overall_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    overall_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    social_accounts: Mapped[List["SocialAccount"]] = relationship(
        "SocialAccount",
        back_populates="influencer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    content_items: Mapped[List["ContentItem"]] = relationship(
        "ContentItem",
        back_populates="influencer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    technologies: Mapped[List["InfluencerTechnology"]] = relationship(
        "InfluencerTechnology",
        back_populates="influencer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    rank_snapshots: Mapped[List["RankSnapshot"]] = relationship(
        "RankSnapshot",
        back_populates="influencer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    relationships: Mapped[List["InfluencerRelationship"]] = relationship(
        "InfluencerRelationship",
        back_populates="influencer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    watchlist_memberships: Mapped[List["WatchlistMember"]] = relationship(
        "WatchlistMember",
        back_populates="influencer",
        cascade="all, delete-orphan"
    )
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        Index(
            'ix_influencers_search_vector',
            'search_vector',
            postgresql_using='gin'
        ),
        Index('ix_influencers_country_region', 'country_code', 'region'),
        Index('ix_influencers_verification_active', 'verification_status', 'is_active'),
        Index('ix_influencers_overall_rank', 'overall_rank'),
    )
    
    def __repr__(self) -> str:
        return f"<Influencer(id={self.id}, name='{self.full_name}')>"
    
    @property
    def primary_social_account(self) -> Optional["SocialAccount"]:
        """Get the primary/most important social account."""
        if not self.social_accounts:
            return None
        # Prefer verified accounts with most followers
        sorted_accounts = sorted(
            self.social_accounts,
            key=lambda a: (a.is_verified, a.followers_count or 0),
            reverse=True
        )
        return sorted_accounts[0] if sorted_accounts else None
    
    @property
    def platform_handles(self) -> dict:
        """Get a dict of platform -> handle mappings."""
        return {
            account.platform: account.handle
            for account in self.social_accounts
            if account.handle
        }


class SocialAccount(Base):
    """Social media account for an influencer."""
    
    __tablename__ = "social_accounts"
    
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
    
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # youtube, github, twitter, linkedin, etc.
    handle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    platform_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Metrics (cached)
    followers_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    following_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    post_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Platform-specific
    account_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )  # personal, business, creator
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    platform_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Sync tracking
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    sync_status: Mapped[str] = mapped_column(
        String(20),
        default="pending"
    )  # pending, syncing, success, error
    sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # API quota tracking
    api_calls_today: Mapped[int] = mapped_column(Integer, default=0)
    api_quota_reset_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
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
        back_populates="social_accounts"
    )
    
    __table_args__ = (
        Index(
            'ix_social_accounts_influencer_platform',
            'influencer_id',
            'platform',
            unique=True
        ),
        Index('ix_social_accounts_platform_handle', 'platform', 'handle'),
        Index('ix_social_accounts_sync_status', 'sync_status'),
    )
    
    def __repr__(self) -> str:
        return f"<SocialAccount(platform='{self.platform}', handle='{self.handle}')>"
