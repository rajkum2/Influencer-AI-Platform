"""
Influencer and Social Account schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import AnyHttpUrl, Field, field_validator

from app.schemas.base import BaseSchema, IDMixin, ListParams, PaginatedResponse, TimestampMixin


class SocialAccountBase(BaseSchema):
    """Base social account schema."""
    
    platform: str = Field(..., min_length=1, max_length=50)
    handle: Optional[str] = Field(None, max_length=255)
    url: AnyHttpUrl
    platform_user_id: Optional[str] = Field(None, max_length=255)


class SocialAccountCreate(SocialAccountBase):
    """Create social account."""
    
    is_verified: bool = False
    account_type: Optional[str] = None


class SocialAccountUpdate(BaseSchema):
    """Update social account."""
    
    handle: Optional[str] = Field(None, max_length=255)
    url: Optional[AnyHttpUrl] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    post_count: Optional[int] = None
    is_verified: Optional[bool] = None
    account_type: Optional[str] = None


class SocialAccountResponse(SocialAccountBase, IDMixin, TimestampMixin):
    """Social account response."""
    
    influencer_id: str
    followers_count: Optional[int]
    following_count: Optional[int]
    post_count: Optional[int]
    is_verified: bool
    is_public: bool
    account_type: Optional[str]
    last_synced_at: Optional[datetime]
    sync_status: str


class InfluencerBase(BaseSchema):
    """Base influencer schema."""
    
    full_name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    headline: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None
    
    # Location
    country_code: Optional[str] = Field(None, max_length=2)
    region: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    
    # Professional
    company: Optional[str] = Field(None, max_length=255)
    role_type: Optional[str] = Field(
        None,
        pattern="^(founder|researcher|educator|engineer|investor|indie|product|marketing)$"
    )
    
    # Contact
    website_url: Optional[AnyHttpUrl] = None
    email_public: Optional[str] = Field(None, max_length=255)
    
    @field_validator('country_code')
    @classmethod
    def validate_country_code(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.upper()
        return v


class InfluencerCreate(InfluencerBase):
    """Create influencer."""
    
    social_accounts: Optional[List[SocialAccountCreate]] = []
    technology_ids: Optional[List[str]] = []


class InfluencerUpdate(BaseSchema):
    """Update influencer."""
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    headline: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None
    country_code: Optional[str] = Field(None, max_length=2)
    region: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=255)
    role_type: Optional[str] = None
    website_url: Optional[AnyHttpUrl] = None
    email_public: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    verification_status: Optional[str] = None


class InfluencerResponse(InfluencerBase, IDMixin, TimestampMixin):
    """Influencer response (list view)."""
    
    profile_image_url: Optional[str]
    verification_status: str
    is_active: bool
    is_featured: bool
    
    # Aggregated stats
    total_followers: int
    content_count: int
    last_content_at: Optional[datetime]
    overall_score: Optional[float]
    overall_rank: Optional[int]
    
    # Related data (simplified)
    social_accounts: List[SocialAccountResponse]
    technologies: List[dict]  # {id, name, relevance_score}
    
    class Config:
        from_attributes = True


class InfluencerDetailResponse(InfluencerResponse):
    """Influencer detail response."""
    
    # Full content timeline (paginated)
    recent_content: List[dict]  # ContentSummary
    
    # Ranking history
    rank_history: List[dict]
    
    # CRM info (if user has access)
    relationship: Optional[dict] = None
    
    # Similar influencers
    similar_influencers: List[dict]


class InfluencerListParams(ListParams):
    """Parameters for influencer list endpoint."""
    
    # Filters
    technology_id: Optional[str] = None
    country_code: Optional[str] = Field(None, max_length=2)
    region: Optional[str] = None
    city: Optional[str] = None
    role_type: Optional[str] = None
    company: Optional[str] = None
    platform: Optional[str] = None
    verification_status: Optional[str] = None
    is_active: Optional[bool] = True
    is_featured: Optional[bool] = None
    
    # Range filters
    min_followers: Optional[int] = Field(None, ge=0)
    max_followers: Optional[int] = Field(None, ge=0)
    min_content_count: Optional[int] = Field(None, ge=0)
    
    # Time filters
    active_since_days: Optional[int] = None
    
    # Sorting options
    sort_by: Optional[str] = Field(
        None,
        pattern="^(created_at|updated_at|full_name|total_followers|content_count|overall_score|overall_rank|last_content_at)$"
    )


class InfluencerSearchParams(BaseSchema):
    """Parameters for influencer search endpoint."""
    
    query: str = Field(..., min_length=1, max_length=200)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    filters: Optional[dict] = None


class InfluencerListResponse(PaginatedResponse[InfluencerResponse]):
    """Paginated influencer list response."""
    
    pass


class InfluencerBulkImportRequest(BaseSchema):
    """Bulk import influencers."""
    
    influencers: List[InfluencerCreate] = Field(..., max_length=100)


class InfluencerBulkUpdateRequest(BaseSchema):
    """Bulk update influencers."""
    
    ids: List[str] = Field(..., min_length=1, max_length=1000)
    updates: InfluencerUpdate


class InfluencerVerificationRequest(BaseSchema):
    """Request to verify an influencer."""
    
    verification_status: str = Field(..., pattern="^(pending|verified|rejected)$")
    notes: Optional[str] = None
