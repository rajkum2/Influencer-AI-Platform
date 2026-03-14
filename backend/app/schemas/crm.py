"""
CRM and Relationship management schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.schemas.base import BaseSchema, IDMixin, ListParams, PaginatedResponse, TimestampMixin


class RelationshipBase(BaseSchema):
    """Base relationship schema."""
    
    stage: str = Field(
        default="not_contacted",
        pattern="^(not_contacted|contacted|responded|meeting|negotiation|partnered|declined|churned)$"
    )
    notes: Optional[str] = None
    opportunity_type: Optional[List[str]] = []
    estimated_value: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD", max_length=3)
    tags: Optional[List[str]] = []


class RelationshipCreate(RelationshipBase):
    """Create relationship."""
    
    influencer_id: str
    source: Optional[str] = Field(None, max_length=100)


class RelationshipUpdate(BaseSchema):
    """Update relationship."""
    
    stage: Optional[str] = None
    notes: Optional[str] = None
    opportunity_type: Optional[List[str]] = None
    estimated_value: Optional[float] = Field(None, ge=0)
    tags: Optional[List[str]] = None
    custom_fields: Optional[dict] = None


class RelationshipStageUpdate(BaseSchema):
    """Update relationship stage."""
    
    stage: str = Field(
        ...,
        pattern="^(not_contacted|contacted|responded|meeting|negotiation|partnered|declined|churned)$"
    )
    notes: Optional[str] = None


class RelationshipResponse(RelationshipBase, IDMixin, TimestampMixin):
    """Relationship response."""
    
    influencer_id: str
    influencer_name: str
    influencer_image_url: Optional[str]
    owner_id: str
    
    # Pipeline
    pipeline_value: Optional[float]
    probability: Optional[int]
    expected_close_date: Optional[datetime]
    actual_close_date: Optional[datetime]
    
    # Follow-up
    last_contacted_at: Optional[datetime]
    next_follow_up_at: Optional[datetime]
    follow_up_reminder_sent: bool
    
    # Calculated
    days_since_contact: Optional[int]
    days_until_follow_up: Optional[int]
    is_open: bool
    
    # Recent interactions
    recent_interactions: List[dict]


class RelationshipListParams(ListParams):
    """Parameters for relationship list endpoint."""
    
    stage: Optional[str] = None
    owner_id: Optional[str] = None
    opportunity_type: Optional[str] = None
    source: Optional[str] = None
    
    # Follow-up filters
    needs_follow_up: Optional[bool] = None
    follow_up_overdue: Optional[bool] = None
    
    # Sorting
    sort_by: Optional[str] = Field(
        None,
        pattern="^(created_at|updated_at|last_contacted_at|next_follow_up_at|estimated_value)$"
    )


class InteractionBase(BaseSchema):
    """Base interaction schema."""
    
    interaction_type: str = Field(
        ...,
        pattern="^(email|dm|call|meeting|video_call|note|task|other)$"
    )
    direction: Optional[str] = Field(
        None,
        pattern="^(inbound|outbound)$"
    )
    subject: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    outcome: Optional[str] = Field(
        None,
        pattern="^(positive|neutral|negative|no_response)$"
    )
    next_steps: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)


class InteractionCreate(InteractionBase):
    """Create interaction."""
    
    relationship_id: str
    occurred_at: Optional[datetime] = None
    attachments: Optional[List[dict]] = []


class InteractionUpdate(BaseSchema):
    """Update interaction."""
    
    subject: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    outcome: Optional[str] = None
    next_steps: Optional[str] = None


class InteractionResponse(InteractionBase, IDMixin):
    """Interaction response."""
    
    relationship_id: str
    occurred_at: datetime
    created_by: str
    created_at: datetime
    attachments: List[dict]


class InteractionListParams(ListParams):
    """Parameters for interaction list endpoint."""
    
    relationship_id: Optional[str] = None
    interaction_type: Optional[str] = None
    direction: Optional[str] = None
    outcome: Optional[str] = None
    created_by: Optional[str] = None
    
    # Time range
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class FollowUpReminderRequest(BaseSchema):
    """Request to set follow-up reminder."""
    
    relationship_id: str
    next_follow_up_at: datetime
    notes: Optional[str] = None


class PipelineStatsResponse(BaseSchema):
    """Pipeline statistics response."""
    
    total_relationships: int
    by_stage: dict  # {stage: count}
    total_value: float
    weighted_value: float  # Sum of value * probability
    avg_deal_size: Optional[float]
    conversion_rate: Optional[float]
