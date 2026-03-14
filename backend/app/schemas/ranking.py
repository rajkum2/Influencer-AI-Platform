"""
Ranking and scoring schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, IDMixin, ListParams, PaginatedResponse


class RankingSnapshotResponse(BaseSchema):
    """Ranking snapshot response."""
    
    calculated_at: datetime
    overall_score: Optional[float]
    overall_rank: Optional[int]
    
    # Component scores
    authority_score: Optional[float]
    relevance_score: Optional[float]
    quality_score: Optional[float]
    engagement_score: Optional[float]
    consistency_score: Optional[float]
    growth_score: Optional[float]
    trust_score: Optional[float]
    
    # Change tracking
    rank_change_7d: Optional[int]
    rank_change_30d: Optional[int]
    score_change_7d: Optional[float]
    score_change_30d: Optional[float]
    
    # Context
    technology_id: Optional[str]
    region: Optional[str]


class RankingConfigBase(BaseSchema):
    """Base ranking config schema."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    
    # Weights
    authority_weight: float = Field(0.25, ge=0, le=1)
    relevance_weight: float = Field(0.20, ge=0, le=1)
    quality_weight: float = Field(0.20, ge=0, le=1)
    engagement_weight: float = Field(0.15, ge=0, le=1)
    consistency_weight: float = Field(0.10, ge=0, le=1)
    growth_weight: float = Field(0.05, ge=0, le=1)
    trust_weight: float = Field(0.05, ge=0, le=1)
    
    # Filters
    technology_id: Optional[str] = None
    region_filter: Optional[str] = None
    country_filter: Optional[str] = Field(None, max_length=2)
    platform_filter: Optional[str] = None
    role_type_filter: Optional[str] = None
    min_followers: Optional[int] = None
    max_followers: Optional[int] = None
    time_range_days: int = Field(90, ge=7, le=365)
    
    @field_validator('authority_weight', 'relevance_weight', 'quality_weight',
                     'engagement_weight', 'consistency_weight', 'growth_weight',
                     'trust_weight', mode='after')
    @classmethod
    def round_weights(cls, v: float) -> float:
        return round(v, 2)


class RankingConfigCreate(RankingConfigBase):
    """Create ranking config."""
    
    is_public: bool = False


class RankingConfigUpdate(BaseSchema):
    """Update ranking config."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    authority_weight: Optional[float] = Field(None, ge=0, le=1)
    relevance_weight: Optional[float] = Field(None, ge=0, le=1)
    quality_weight: Optional[float] = Field(None, ge=0, le=1)
    engagement_weight: Optional[float] = Field(None, ge=0, le=1)
    consistency_weight: Optional[float] = Field(None, ge=0, le=1)
    growth_weight: Optional[float] = Field(None, ge=0, le=1)
    trust_weight: Optional[float] = Field(None, ge=0, le=1)
    is_public: Optional[bool] = None


class RankingConfigResponse(RankingConfigBase, IDMixin):
    """Ranking config response."""
    
    created_by: str
    is_public: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    @property
    def total_weight(self) -> float:
        return round(
            self.authority_weight + self.relevance_weight +
            self.quality_weight + self.engagement_weight +
            self.consistency_weight + self.growth_weight +
            self.trust_weight,
            2
        )


class RankingHistoryParams(ListParams):
    """Parameters for ranking history endpoint."""
    
    influencer_id: Optional[str] = None
    technology_id: Optional[str] = None
    region: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class RankingLeaderboardResponse(BaseSchema):
    """Ranking leaderboard response."""
    
    config_id: Optional[str]
    technology_id: Optional[str]
    region: Optional[str]
    calculated_at: datetime
    influencers: List[dict]  # {rank, influencer_id, name, score, change}


class RankingCalculationRequest(BaseSchema):
    """Request to trigger ranking calculation."""
    
    config_id: Optional[str] = None  # null = default calculation
    influencer_ids: Optional[List[str]] = None  # null = all
    full_recalculation: bool = False


class RankingCalculationResponse(BaseSchema):
    """Ranking calculation response."""
    
    job_id: str
    status: str
    message: str
