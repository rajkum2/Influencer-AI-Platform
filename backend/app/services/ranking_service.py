"""
Ranking service for business logic.
"""

from datetime import datetime, timedelta
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.influencer import Influencer
from app.models.ranking import RankingConfig, RankSnapshot
from app.schemas.ranking import (
    RankingConfigCreate,
    RankingConfigUpdate,
)

logger = get_logger(__name__)


class RankingService:
    """Service for ranking operations."""
    
    # Default weights
    DEFAULT_WEIGHTS = {
        "authority": 0.25,
        "relevance": 0.20,
        "quality": 0.20,
        "engagement": 0.15,
        "consistency": 0.10,
        "growth": 0.05,
        "trust": 0.05
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_rankings(
        self,
        technology_id: Optional[UUID] = None,
        region: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> dict:
        """Get current rankings."""
        
        # Get latest snapshot for each influencer
        subquery = select(
            RankSnapshot.influencer_id,
            func.max(RankSnapshot.calculated_at).label("max_date")
        ).where(
            and_(
                RankSnapshot.technology_id == technology_id,
                RankSnapshot.region == region
            )
        ).group_by(RankSnapshot.influencer_id).subquery()
        
        query = select(RankSnapshot, Influencer).join(
            subquery,
            and_(
                RankSnapshot.influencer_id == subquery.c.influencer_id,
                RankSnapshot.calculated_at == subquery.c.max_date
            )
        ).join(Influencer).where(
            Influencer.is_active == True
        ).order_by(RankSnapshot.overall_rank)
        
        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        items = [
            {
                "rank": row.RankSnapshot.overall_rank,
                "influencer_id": str(row.Influencer.id),
                "full_name": row.Influencer.full_name,
                "profile_image_url": row.Influencer.profile_image_url,
                "total_followers": row.Influencer.total_followers,
                "overall_score": row.RankSnapshot.overall_score,
                "scores": {
                    "authority": row.RankSnapshot.authority_score,
                    "relevance": row.RankSnapshot.relevance_score,
                    "quality": row.RankSnapshot.quality_score,
                    "engagement": row.RankSnapshot.engagement_score,
                    "consistency": row.RankSnapshot.consistency_score,
                    "growth": row.RankSnapshot.growth_score,
                    "trust": row.RankSnapshot.trust_score
                },
                "rank_change_7d": row.RankSnapshot.rank_change_7d,
                "rank_change_30d": row.RankSnapshot.rank_change_30d
            }
            for row in rows
        ]
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "technology_id": str(technology_id) if technology_id else None,
            "region": region
        }
    
    async def get_influencer_history(
        self,
        influencer_id: UUID,
        days: int = 30
    ) -> List[dict]:
        """Get ranking history for an influencer."""
        
        since = datetime.utcnow() - timedelta(days=days)
        
        query = select(RankSnapshot).where(
            and_(
                RankSnapshot.influencer_id == influencer_id,
                RankSnapshot.calculated_at >= since,
                RankSnapshot.technology_id.is_(None),  # Global rankings
                RankSnapshot.region.is_(None)
            )
        ).order_by(RankSnapshot.calculated_at)
        
        result = await self.db.execute(query)
        snapshots = result.scalars().all()
        
        return [
            {
                "calculated_at": s.calculated_at,
                "overall_score": s.overall_score,
                "overall_rank": s.overall_rank,
                "authority_score": s.authority_score,
                "relevance_score": s.relevance_score,
                "quality_score": s.quality_score,
                "engagement_score": s.engagement_score,
                "consistency_score": s.consistency_score,
                "growth_score": s.growth_score,
                "trust_score": s.trust_score,
                "rank_change_7d": s.rank_change_7d,
                "rank_change_30d": s.rank_change_30d
            }
            for s in snapshots
        ]
    
    async def get_user_configs(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """Get ranking configs for a user."""
        
        query = select(RankingConfig).where(
            and_(
                RankingConfig.created_by == user_id,
                RankingConfig.is_public == False
            )
        )
        
        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        configs = result.scalars().all()
        
        return {
            "items": configs,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def get_config(self, config_id: UUID) -> Optional[RankingConfig]:
        """Get ranking config by ID."""
        query = select(RankingConfig).where(RankingConfig.id == config_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_config(
        self,
        data: RankingConfigCreate,
        user_id: UUID
    ) -> RankingConfig:
        """Create ranking config."""
        
        config = RankingConfig(
            name=data.name,
            description=data.description,
            authority_weight=data.authority_weight,
            relevance_weight=data.relevance_weight,
            quality_weight=data.quality_weight,
            engagement_weight=data.engagement_weight,
            consistency_weight=data.consistency_weight,
            growth_weight=data.growth_weight,
            trust_weight=data.trust_weight,
            technology_id=UUID(data.technology_id) if data.technology_id else None,
            region_filter=data.region_filter,
            country_filter=data.country_filter,
            platform_filter=data.platform_filter,
            role_type_filter=data.role_type_filter,
            min_followers=data.min_followers,
            max_followers=data.max_followers,
            time_range_days=data.time_range_days,
            created_by=user_id,
            is_public=data.is_public
        )
        
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        
        return config
    
    async def update_config(
        self,
        config_id: UUID,
        data: RankingConfigUpdate
    ) -> Optional[RankingConfig]:
        """Update ranking config."""
        
        config = await self.get_config(config_id)
        if not config:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(config, field, value)
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return config
    
    async def delete_config(self, config_id: UUID) -> bool:
        """Delete ranking config."""
        
        config = await self.get_config(config_id)
        if not config:
            return False
        
        await self.db.delete(config)
        await self.db.commit()
        
        return True
    
    async def calculate_scores(
        self,
        influencer_id: UUID,
        weights: dict = None
    ) -> dict:
        """Calculate ranking scores for an influencer."""
        
        weights = weights or self.DEFAULT_WEIGHTS
        
        influencer = await self.db.get(Influencer, influencer_id)
        if not influencer:
            return None
        
        # Calculate individual scores (0-100 scale)
        authority_score = self._calculate_authority(influencer)
        relevance_score = self._calculate_relevance(influencer)
        quality_score = self._calculate_quality(influencer)
        engagement_score = self._calculate_engagement(influencer)
        consistency_score = self._calculate_consistency(influencer)
        growth_score = self._calculate_growth(influencer)
        trust_score = self._calculate_trust(influencer)
        
        # Calculate weighted overall score
        overall_score = (
            authority_score * weights.get("authority", 0.25) +
            relevance_score * weights.get("relevance", 0.20) +
            quality_score * weights.get("quality", 0.20) +
            engagement_score * weights.get("engagement", 0.15) +
            consistency_score * weights.get("consistency", 0.10) +
            growth_score * weights.get("growth", 0.05) +
            trust_score * weights.get("trust", 0.05)
        )
        
        return {
            "overall": round(overall_score, 3),
            "authority": round(authority_score, 3),
            "relevance": round(relevance_score, 3),
            "quality": round(quality_score, 3),
            "engagement": round(engagement_score, 3),
            "consistency": round(consistency_score, 3),
            "growth": round(growth_score, 3),
            "trust": round(trust_score, 3)
        }
    
    def _calculate_authority(self, influencer: Influencer) -> float:
        """Calculate authority score based on followers and verification."""
        score = min(100, (influencer.total_followers or 0) / 1000)
        
        # Boost for verified accounts
        verified_platforms = sum(
            1 for acc in influencer.social_accounts if acc.is_verified
        )
        score += verified_platforms * 5
        
        return min(100, score)
    
    def _calculate_relevance(self, influencer: Influencer) -> float:
        """Calculate relevance score based on technology focus."""
        if not influencer.technologies:
            return 50.0
        
        avg_relevance = sum(
            t.relevance_score or 0.5 for t in influencer.technologies
        ) / len(influencer.technologies)
        
        return avg_relevance * 100
    
    def _calculate_quality(self, influencer: Influencer) -> float:
        """Calculate content quality score."""
        # This would ideally use AI-scored content quality
        # For now, use a placeholder based on content count
        if influencer.content_count == 0:
            return 50.0
        
        return min(100, 50 + influencer.content_count * 0.5)
    
    def _calculate_engagement(self, influencer: Influencer) -> float:
        """Calculate engagement score."""
        # Placeholder - would use actual engagement metrics
        return 60.0
    
    def _calculate_consistency(self, influencer: Influencer) -> float:
        """Calculate consistency score based on posting frequency."""
        if not influencer.last_content_at:
            return 30.0
        
        days_since = (datetime.utcnow() - influencer.last_content_at).days
        
        if days_since <= 7:
            return 100.0
        elif days_since <= 30:
            return 80.0
        elif days_since <= 90:
            return 60.0
        else:
            return max(30, 100 - days_since * 0.5)
    
    def _calculate_growth(self, influencer: Influencer) -> float:
        """Calculate growth score."""
        # Placeholder - would calculate based on follower growth
        return 50.0
    
    def _calculate_trust(self, influencer: Influencer) -> float:
        """Calculate trust score based on verification and data quality."""
        score = 50.0
        
        if influencer.verification_status == "verified":
            score += 30
        
        # Boost for having multiple verified platforms
        verified_count = sum(
            1 for acc in influencer.social_accounts if acc.is_verified
        )
        score += verified_count * 5
        
        return min(100, score)
