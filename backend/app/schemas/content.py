"""
Content and Content Engagement schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import AnyHttpUrl, Field

from app.schemas.base import BaseSchema, IDMixin, ListParams, PaginatedResponse, TimestampMixin


class ContentTechnologyCreate(BaseSchema):
    """Create content-technology association."""
    
    technology_id: str
    relevance_score: Optional[float] = Field(None, ge=0, le=1)
    confidence: Optional[float] = Field(None, ge=0, le=1)


class ContentBase(BaseSchema):
    """Base content schema."""
    
    platform: str = Field(..., min_length=1, max_length=50)
    content_type: str = Field(..., min_length=1, max_length=50)
    external_id: str = Field(..., max_length=255)
    original_url: AnyHttpUrl
    title: Optional[str] = Field(None, max_length=500)
    body_text: Optional[str] = None
    published_at: Optional[datetime] = None


class ContentCreate(ContentBase):
    """Create content item."""
    
    influencer_id: str
    social_account_id: Optional[str] = None
    thumbnail_url: Optional[AnyHttpUrl] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    language_code: Optional[str] = Field(None, max_length=2)
    technologies: Optional[List[ContentTechnologyCreate]] = []


class ContentUpdate(BaseSchema):
    """Update content item."""
    
    title: Optional[str] = Field(None, max_length=500)
    body_text: Optional[str] = None
    summary: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=0, le=1)
    is_indexed: Optional[bool] = None
    processing_status: Optional[str] = None


class ContentEngagementResponse(BaseSchema):
    """Content engagement metrics."""
    
    views: Optional[int]
    likes: Optional[int]
    comments: Optional[int]
    shares: Optional[int]
    engagement_rate: Optional[float]
    measured_at: datetime


class ContentSummary(BaseSchema, IDMixin):
    """Simplified content for lists."""
    
    platform: str
    content_type: str
    title: Optional[str]
    thumbnail_url: Optional[str]
    published_at: Optional[datetime]
    summary: Optional[str]
    views: Optional[int]
    likes: Optional[int]


class ContentResponse(ContentBase, IDMixin, TimestampMixin):
    """Content item response."""
    
    influencer_id: str
    influencer_name: str
    social_account_id: Optional[str]
    
    thumbnail_url: Optional[str]
    duration_seconds: Optional[int]
    language_code: Optional[str]
    country_hint: Optional[str]
    
    # AI Enrichment
    summary: Optional[str]
    quality_score: Optional[float]
    spam_score: Optional[float]
    
    # Engagement (latest)
    views: Optional[int]
    likes: Optional[int]
    comments: Optional[int]
    shares: Optional[int]
    engagement_rate: Optional[float]
    
    # Technologies
    technologies: List[dict]
    
    # Status
    processing_status: str
    is_indexed: bool


class ContentListParams(ListParams):
    """Parameters for content list endpoint."""
    
    # Filters
    influencer_id: Optional[str] = None
    platform: Optional[str] = None
    content_type: Optional[str] = None
    technology_id: Optional[str] = None
    language_code: Optional[str] = Field(None, max_length=2)
    
    # Time range
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    # Quality
    min_quality_score: Optional[float] = Field(None, ge=0, le=1)
    is_processed: Optional[bool] = None
    
    # Sorting
    sort_by: Optional[str] = Field(
        None,
        pattern="^(published_at|created_at|views|likes|quality_score)$"
    )


class ContentListResponse(PaginatedResponse[ContentResponse]):
    """Paginated content list response."""
    
    pass


class ContentFeedResponse(BaseSchema):
    """Content feed response (for dashboard)."""
    
    items: List[ContentResponse]
    date_grouped: dict  # {date: [content_items]}
    total_new_today: int
    total_new_week: int


class ContentClassificationRequest(BaseSchema):
    """Request to classify content."""
    
    content_ids: List[str] = Field(..., min_length=1, max_length=100)


class ContentClassificationResponse(BaseSchema):
    """Content classification response."""
    
    content_id: str
    technologies: List[dict]
    summary: Optional[str]
    processing_time_ms: int
