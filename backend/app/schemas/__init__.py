"""
Pydantic schemas for request/response validation.
"""

from app.schemas.auth import (
    LoginRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.content import (
    ContentCreate,
    ContentEngagementResponse,
    ContentListParams,
    ContentResponse,
    ContentSummary,
    ContentTechnologyCreate,
    ContentUpdate,
)
from app.schemas.crm import (
    InteractionCreate,
    InteractionResponse,
    InteractionUpdate,
    RelationshipCreate,
    RelationshipListParams,
    RelationshipResponse,
    RelationshipStageUpdate,
    RelationshipUpdate,
)
from app.schemas.influencer import (
    InfluencerCreate,
    InfluencerDetailResponse,
    InfluencerListParams,
    InfluencerResponse,
    InfluencerSearchParams,
    InfluencerUpdate,
    SocialAccountCreate,
    SocialAccountResponse,
    SocialAccountUpdate,
)
from app.schemas.ranking import (
    RankingConfigCreate,
    RankingConfigResponse,
    RankingConfigUpdate,
    RankingHistoryParams,
    RankingSnapshotResponse,
)
from app.schemas.technology import (
    TechnologyCreate,
    TechnologyListParams,
    TechnologyResponse,
    TechnologyUpdate,
)
from app.schemas.user import (
    TeamCreate,
    TeamResponse,
    TeamUpdate,
    UserCreate,
    UserPreferencesUpdate,
    UserResponse,
    UserUpdate,
)
from app.schemas.watchlist import (
    WatchlistAddMember,
    WatchlistCreate,
    WatchlistMemberResponse,
    WatchlistResponse,
    WatchlistUpdate,
)

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "PasswordResetRequest",
    # Influencer
    "InfluencerCreate",
    "InfluencerUpdate",
    "InfluencerResponse",
    "InfluencerDetailResponse",
    "InfluencerListParams",
    "InfluencerSearchParams",
    "SocialAccountCreate",
    "SocialAccountUpdate",
    "SocialAccountResponse",
    # Content
    "ContentCreate",
    "ContentUpdate",
    "ContentResponse",
    "ContentSummary",
    "ContentListParams",
    "ContentEngagementResponse",
    "ContentTechnologyCreate",
    # Technology
    "TechnologyCreate",
    "TechnologyUpdate",
    "TechnologyResponse",
    "TechnologyListParams",
    # Ranking
    "RankingConfigCreate",
    "RankingConfigUpdate",
    "RankingConfigResponse",
    "RankingSnapshotResponse",
    "RankingHistoryParams",
    # CRM
    "RelationshipCreate",
    "RelationshipUpdate",
    "RelationshipResponse",
    "RelationshipStageUpdate",
    "RelationshipListParams",
    "InteractionCreate",
    "InteractionUpdate",
    "InteractionResponse",
    # Watchlist
    "WatchlistCreate",
    "WatchlistUpdate",
    "WatchlistResponse",
    "WatchlistMemberResponse",
    "WatchlistAddMember",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserPreferencesUpdate",
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
]
