"""
Watchlist and saved lists schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.schemas.base import BaseSchema, IDMixin, TimestampMixin


class WatchlistBase(BaseSchema):
    """Base watchlist schema."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class WatchlistCreate(WatchlistBase):
    """Create watchlist."""
    
    team_id: Optional[str] = None
    is_dynamic: bool = False
    filter_criteria: Optional[dict] = {}
    alert_config: Optional[dict] = {}


class WatchlistUpdate(BaseSchema):
    """Update watchlist."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    is_shared: Optional[bool] = None
    alert_config: Optional[dict] = None
    filter_criteria: Optional[dict] = None


class WatchlistAddMember(BaseSchema):
    """Add member to watchlist."""
    
    influencer_id: str
    notes: Optional[str] = None
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    tags: Optional[List[str]] = []


class WatchlistMemberResponse(BaseSchema):
    """Watchlist member response."""
    
    id: str
    influencer_id: str
    influencer_name: str
    influencer_headline: Optional[str]
    profile_image_url: Optional[str]
    overall_score: Optional[float]
    added_at: datetime
    added_by: str
    notes: Optional[str]
    priority: str
    tags: List[str]


class WatchlistResponse(WatchlistBase, IDMixin, TimestampMixin):
    """Watchlist response."""
    
    owner_id: str
    team_id: Optional[str]
    is_shared: bool
    share_permission: str
    is_dynamic: bool
    member_count: int
    
    # Dynamic list config
    filter_criteria: dict
    alert_config: dict
    
    # Members (optional, for detail view)
    members: Optional[List[WatchlistMemberResponse]] = None


class WatchlistListResponse(BaseSchema):
    """Watchlist list response."""
    
    watchlists: List[WatchlistResponse]
    total: int


class WatchlistAlertConfig(BaseSchema):
    """Watchlist alert configuration."""
    
    new_content: bool = True
    rank_change: dict = Field(default_factory=lambda: {"enabled": True, "threshold": 10})
    follower_milestone: dict = Field(default_factory=lambda: {"enabled": True, "threshold": 10000})
    new_platform: bool = True
    job_change: bool = True


class WatchlistComparisonRequest(BaseSchema):
    """Request to compare watchlists."""
    
    watchlist_ids: List[str] = Field(..., min_length=2, max_length=5)
    metrics: List[str] = ["followers", "engagement", "content_count", "growth"]


class WatchlistComparisonResponse(BaseSchema):
    """Watchlist comparison response."""
    
    watchlists: List[dict]
    metrics: dict
    overlapping_influencers: List[dict]
