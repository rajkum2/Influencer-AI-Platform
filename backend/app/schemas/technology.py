"""
Technology/Topic taxonomy schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.schemas.base import BaseSchema, IDMixin, ListParams, PaginatedResponse


class TechnologyBase(BaseSchema):
    """Base technology schema."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    keywords: Optional[List[str]] = []
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=100)


class TechnologyCreate(TechnologyBase):
    """Create technology."""
    
    slug: Optional[str] = Field(None, max_length=100)
    parent_id: Optional[str] = None


class TechnologyUpdate(BaseSchema):
    """Update technology."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=100)


class TechnologyResponse(TechnologyBase, IDMixin):
    """Technology response."""
    
    slug: str
    parent_id: Optional[str]
    influencer_count: int
    content_count: int
    is_active: bool
    display_order: int
    created_at: datetime
    
    # Tree structure
    children: Optional[List["TechnologyResponse"]] = None


class TechnologyListParams(ListParams):
    """Parameters for technology list endpoint."""
    
    is_active: Optional[bool] = True
    parent_id: Optional[str] = None
    has_content: Optional[bool] = None


class TechnologyTreeResponse(BaseSchema):
    """Technology tree response."""
    
    technologies: List[TechnologyResponse]


class TechnologyInfluencerResponse(BaseSchema):
    """Influencer with technology relevance."""
    
    influencer_id: str
    influencer_name: str
    profile_image_url: Optional[str]
    relevance_score: float
    content_count: int


class TechnologyContentResponse(BaseSchema):
    """Content with technology relevance."""
    
    content_id: str
    title: Optional[str]
    platform: str
    published_at: Optional[datetime]
    relevance_score: float
