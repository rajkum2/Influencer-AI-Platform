"""
Rankings endpoints.
"""

from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_active_user
from app.db.base import get_db
from app.schemas.ranking import (
    RankingCalculationRequest,
    RankingCalculationResponse,
    RankingConfigCreate,
    RankingConfigResponse,
    RankingConfigUpdate,
    RankingHistoryParams,
    RankingSnapshotResponse,
)
from app.services.ranking_service import RankingService

router = APIRouter()


@router.get("", response_model=dict)
async def get_rankings(
    technology_id: Optional[str] = None,
    region: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get influencer rankings.
    """
    service = RankingService(db)
    result = await service.get_rankings(
        technology_id=UUID(technology_id) if technology_id else None,
        region=region,
        page=page,
        page_size=page_size
    )
    
    return result


@router.get("/configs", response_model=dict)
async def list_ranking_configs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List custom ranking configurations.
    """
    service = RankingService(db)
    configs = await service.get_user_configs(
        user_id=UUID(current_user["id"]),
        page=page,
        page_size=page_size
    )
    
    return configs


@router.post("/configs", response_model=RankingConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_ranking_config(
    data: RankingConfigCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create custom ranking configuration.
    """
    service = RankingService(db)
    
    config = await service.create_config(data, user_id=UUID(current_user["id"]))
    return config


@router.get("/configs/{config_id}", response_model=RankingConfigResponse)
async def get_ranking_config(
    config_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get ranking configuration.
    """
    service = RankingService(db)
    config = await service.get_config(UUID(config_id))
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ranking configuration not found"
        )
    
    return config


@router.put("/configs/{config_id}", response_model=RankingConfigResponse)
async def update_ranking_config(
    config_id: str,
    data: RankingConfigUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update ranking configuration.
    """
    service = RankingService(db)
    
    config = await service.update_config(UUID(config_id), data)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ranking configuration not found"
        )
    
    return config


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ranking_config(
    config_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete ranking configuration.
    """
    service = RankingService(db)
    
    success = await service.delete_config(UUID(config_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ranking configuration not found"
        )


@router.post("/calculate", response_model=RankingCalculationResponse)
async def trigger_ranking_calculation(
    request: RankingCalculationRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Trigger ranking calculation.
    """
    from app.workers.tasks import calculate_rankings
    
    # Queue ranking calculation
    task = calculate_rankings.delay(
        config_id=request.config_id,
        influencer_ids=request.influencer_ids,
        full_recalculation=request.full_recalculation
    )
    
    return RankingCalculationResponse(
        job_id=task.id,
        status="queued",
        message="Ranking calculation queued"
    )


@router.get("/{influencer_id}/history", response_model=List[RankingSnapshotResponse])
async def get_influencer_rank_history(
    influencer_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get ranking history for an influencer.
    """
    service = RankingService(db)
    history = await service.get_influencer_history(UUID(influencer_id), days)
    
    return history
