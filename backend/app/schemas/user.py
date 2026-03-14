"""
User and Team schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseSchema, IDMixin, ListParams, PaginatedResponse, TimestampMixin


class TeamBase(BaseSchema):
    """Base team schema."""
    
    name: str = Field(..., min_length=1, max_length=100)


class TeamCreate(TeamBase):
    """Create team."""
    
    slug: Optional[str] = Field(None, max_length=100)


class TeamUpdate(BaseSchema):
    """Update team."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    settings: Optional[dict] = None


class TeamResponse(TeamBase, IDMixin, TimestampMixin):
    """Team response."""
    
    slug: str
    plan: str
    max_influencers: int
    max_team_members: int
    max_watchlists: int
    settings: dict
    member_count: int


class TeamMemberResponse(BaseSchema):
    """Team member response."""
    
    user_id: str
    email: str
    full_name: str
    avatar_url: Optional[str]
    team_role: str
    joined_at: datetime


class UserBase(BaseSchema):
    """Base user schema."""
    
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Create user."""
    
    password: str = Field(..., min_length=8)
    team_id: Optional[str] = None
    role: str = Field("member", pattern="^(superadmin|admin|member|viewer)$")


class UserUpdate(BaseSchema):
    """Update user."""
    
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    role: Optional[str] = Field(
        None,
        pattern="^(superadmin|admin|member|viewer)$"
    )
    is_active: Optional[bool] = None


class UserPreferencesUpdate(BaseSchema):
    """Update user preferences."""
    
    preferences: dict
    notification_settings: Optional[dict] = None


class UserResponse(UserBase, IDMixin, TimestampMixin):
    """User response."""
    
    full_name: str
    avatar_url: Optional[str]
    role: str
    team_id: Optional[str]
    is_active: bool
    email_verified_at: Optional[datetime]
    last_login_at: Optional[datetime]
    preferences: dict
    notification_settings: dict


class UserListParams(ListParams):
    """Parameters for user list endpoint."""
    
    team_id: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class InviteUserRequest(BaseSchema):
    """Request to invite a user."""
    
    email: EmailStr
    role: str = Field("member", pattern="^(admin|member|viewer)$")
    team_role: str = Field("member", pattern="^(owner|admin|member)$")
    message: Optional[str] = None


class InviteUserResponse(BaseSchema):
    """Invite user response."""
    
    invite_token: str
    invite_url: str
    expires_at: datetime


class AcceptInviteRequest(BaseSchema):
    """Request to accept invitation."""
    
    token: str
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)


class NotificationPreference(BaseSchema):
    """Notification preference."""
    
    email: bool = True
    push: bool = True
    digest_frequency: str = Field("daily", pattern="^(realtime|daily|weekly|never)$")
    
    # Event types
    new_content: bool = True
    rank_changes: bool = True
    follow_up_reminders: bool = True
    team_mentions: bool = True
    system_updates: bool = True
