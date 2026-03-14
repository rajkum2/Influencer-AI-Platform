"""
Authentication-related schemas.
"""

from typing import Optional

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema


class LoginRequest(BaseSchema):
    """Login request."""
    
    email: EmailStr
    password: str = Field(..., min_length=8)
    remember_me: bool = False


class TokenResponse(BaseSchema):
    """Token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user_id: str
    email: str
    role: str


class RefreshTokenRequest(BaseSchema):
    """Refresh token request."""
    
    refresh_token: str


class PasswordResetRequest(BaseSchema):
    """Password reset request."""
    
    email: EmailStr


class PasswordResetConfirm(BaseSchema):
    """Password reset confirmation."""
    
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseSchema):
    """Change password request."""
    
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class UserProfileResponse(BaseSchema):
    """User profile response."""
    
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: str
    avatar_url: Optional[str]
    role: str
    team_id: Optional[str]
    email_verified: bool
    preferences: dict
