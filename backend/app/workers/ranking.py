"""
Ranking calculation workers.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import SessionLocal
from app.models.influencer import Influencer
from app.models.ranking import RankingConfig, RankSnapshot
from app.services.ranking_service import RankingService
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=2)
def calculate_all_rankings(self) -> dict:
    """
    Calculate rankings for all influencers.
    """
    import asyncio
    return asyncio.run(_calculate_all_rankings())


async def _calculate_all_rankings() -> dict:
    """Async implementation of ranking calculation."""
    
    async with SessionLocal() as db:
        # Get all active influencers
        result = await db.execute(
            select(Influencer).where(Influencer.is_active == True)
        )
        influencers = result.scalars().all()
        
        ranking_service = RankingService(db)
        
        calculated = 0
        failed = 0
        
        for influencer in influencers:
            try:
                await _calculate_influencer_ranking(
                    db, influencer, ranking_service
                )
                calculated += 1
            except Exception as e:
                logger.error(
                    "Ranking calculation failed",
                    influencer_id=str(influencer.id),
                    error=str(e)
                )
                failed += 1
        
        # Recalculate ranks based on overall scores
        await _recalculate_ranks(db)
        
        logger.info(
            "Ranking calculation completed",
            total=len(influencers),
            calculated=calculated,
            failed=failed
        )
        
        return {
            "total": len(influencers),
            "calculated": calculated,
            "failed": failed
        }


async def _calculate_influencer_ranking(
    db: AsyncSession,
    influencer: Influencer,
    ranking_service: RankingService
) -> None:
    """Calculate ranking for a single influencer."""
    
    # Calculate scores
    scores = await ranking_service.calculate_scores(influencer.id)
    
    if not scores:
        return
    
    # Get previous snapshot for change tracking
    previous = await db.execute(
        select(RankSnapshot).where(
            RankSnapshot.influencer_id == influencer.id
        ).order_by(RankSnapshot.calculated_at.desc()).limit(1)
    )
    previous_snapshot = previous.scalar_one_or_none()
    
    # Calculate changes
    score_change_7d = None
    score_change_30d = None
    
    if previous_snapshot:
        score_change_7d = scores["overall"] - (previous_snapshot.overall_score or 0)
        score_change_30d = score_change_7d  # Simplified
    
    # Create snapshot
    snapshot = RankSnapshot(
        influencer_id=influencer.id,
        calculated_at=datetime.utcnow(),
        overall_score=scores["overall"],
        authority_score=scores["authority"],
        relevance_score=scores["relevance"],
        quality_score=scores["quality"],
        engagement_score=scores["engagement"],
        consistency_score=scores["consistency"],
        growth_score=scores["growth"],
        trust_score=scores["trust"],
        score_change_7d=score_change_7d,
        score_change_30d=score_change_30d
    )
    
    db.add(snapshot)
    
    # Update influencer's current score
    influencer.overall_score = scores["overall"]
    
    await db.commit()


async def _recalculate_ranks(db: AsyncSession) -> None:
    """Recalculate overall ranks based on scores."""
    
    # Get latest snapshot for each influencer
    from sqlalchemy import func, desc
    
    subquery = select(
        RankSnapshot.influencer_id,
        func.max(RankSnapshot.calculated_at).label("max_date")
    ).group_by(RankSnapshot.influencer_id).subquery()
    
    result = await db.execute(
        select(RankSnapshot).join(
            subquery,
            (RankSnapshot.influencer_id == subquery.c.influencer_id) &
            (RankSnapshot.calculated_at == subquery.c.max_date)
        ).order_by(desc(RankSnapshot.overall_score))
    )
    
    snapshots = result.scalars().all()
    
    # Assign ranks
    for rank, snapshot in enumerate(snapshots, start=1):
        snapshot.overall_rank = rank
        
        # Calculate rank changes
        # Get snapshot from 7 days ago
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_ago_snapshot = await db.execute(
            select(RankSnapshot).where(
                (RankSnapshot.influencer_id == snapshot.influencer_id) &
                (RankSnapshot.calculated_at <= week_ago)
            ).order_by(desc(RankSnapshot.calculated_at)).limit(1)
        )
        week_ago = week_ago_snapshot.scalar_one_or_none()
        
        if week_ago and week_ago.overall_rank:
            snapshot.rank_change_7d = week_ago.overall_rank - rank
    
    await db.commit()


def process_ranking_calculation(
    config_id: Optional[str] = None,
    influencer_ids: Optional[List[str]] = None,
    full_recalculation: bool = False
) -> dict:
    """Process ranking calculation request."""
    import asyncio
    return asyncio.run(_process_ranking_calculation(
        config_id, influencer_ids, full_recalculation
    ))


async def _process_ranking_calculation(
    config_id: Optional[str],
    influencer_ids: Optional[List[str]],
    full_recalculation: bool
) -> dict:
    """Async implementation of ranking calculation."""
    
    async with SessionLocal() as db:
        ranking_service = RankingService(db)
        
        # Get config if specified
        weights = None
        if config_id:
            config = await db.get(RankingConfig, UUID(config_id))
            if config:
                weights = {
                    "authority": config.authority_weight,
                    "relevance": config.relevance_weight,
                    "quality": config.quality_weight,
                    "engagement": config.engagement_weight,
                    "consistency": config.consistency_weight,
                    "growth": config.growth_weight,
                    "trust": config.trust_weight
                }
        
        # Get influencers
        if influencer_ids:
            influencers = []
            for inf_id in influencer_ids:
                inf = await db.get(Influencer, UUID(inf_id))
                if inf:
                    influencers.append(inf)
        else:
            result = await db.execute(
                select(Influencer).where(Influencer.is_active == True)
            )
            influencers = result.scalars().all()
        
        calculated = 0
        
        for influencer in influencers:
            try:
                scores = await ranking_service.calculate_scores(
                    influencer.id, weights
                )
                
                if scores:
                    # Create snapshot
                    snapshot = RankSnapshot(
                        influencer_id=influencer.id,
                        calculated_at=datetime.utcnow(),
                        overall_score=scores["overall"],
                        authority_score=scores["authority"],
                        relevance_score=scores["relevance"],
                        quality_score=scores["quality"],
                        engagement_score=scores["engagement"],
                        consistency_score=scores["consistency"],
                        growth_score=scores["growth"],
                        trust_score=scores["trust"]
                    )
                    db.add(snapshot)
                    
                    influencer.overall_score = scores["overall"]
                    calculated += 1
            except Exception as e:
                logger.error(
                    "Ranking calculation failed",
                    influencer_id=str(influencer.id),
                    error=str(e)
                )
        
        await db.commit()
        
        if full_recalculation:
            await _recalculate_ranks(db)
        
        return {"count": calculated}
