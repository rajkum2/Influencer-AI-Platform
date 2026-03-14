"""
Influencer endpoints.
"""

from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_active_user, require_admin
from app.core.logging import get_logger
from app.db.base import get_db
from app.schemas.influencer import (
    InfluencerBulkImportRequest,
    InfluencerCreate,
    InfluencerDetailResponse,
    InfluencerListParams,
    InfluencerResponse,
    InfluencerUpdate,
    InfluencerVerificationRequest,
    SocialAccountCreate,
    SocialAccountResponse,
    SocialAccountUpdate,
)
from app.services.influencer_service import InfluencerService

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=dict)
async def list_influencers(
    params: InfluencerListParams = Depends(),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List influencers with filtering and pagination.
    """
    service = InfluencerService(db)
    result = await service.get_influencers(params)
    
    return {
        "items": result["items"],
        "total": result["total"],
        "page": params.page,
        "page_size": params.page_size,
        "pages": (result["total"] + params.page_size - 1) // params.page_size,
        "has_next": params.page * params.page_size < result["total"],
        "has_prev": params.page > 1
    }


@router.get("/search", response_model=dict)
async def search_influencers(
    query: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Search influencers by name, bio, or other fields.
    """
    service = InfluencerService(db)
    result = await service.search(query, page, page_size)
    
    return {
        "items": result["items"],
        "total": result["total"],
        "page": page,
        "page_size": page_size,
        "query": query
    }


@router.post("", response_model=InfluencerResponse, status_code=status.HTTP_201_CREATED)
async def create_influencer(
    data: InfluencerCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new influencer profile.
    """
    service = InfluencerService(db)
    
    try:
        influencer = await service.create(data, created_by=UUID(current_user["id"]))
        return influencer
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{influencer_id}", response_model=InfluencerDetailResponse)
async def get_influencer(
    influencer_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get detailed influencer information.
    """
    service = InfluencerService(db)
    influencer = await service.get_by_id(UUID(influencer_id))
    
    if not influencer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Influencer not found"
        )
    
    return influencer


@router.put("/{influencer_id}", response_model=InfluencerResponse)
async def update_influencer(
    influencer_id: str,
    data: InfluencerUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update an influencer profile.
    """
    service = InfluencerService(db)
    
    try:
        influencer = await service.update(UUID(influencer_id), data)
        if not influencer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Influencer not found"
            )
        return influencer
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{influencer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_influencer(
    influencer_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete an influencer profile (admin only).
    """
    service = InfluencerService(db)
    
    success = await service.delete(UUID(influencer_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Influencer not found"
        )


@router.post("/{influencer_id}/verify", response_model=InfluencerResponse)
async def verify_influencer(
    influencer_id: str,
    data: InfluencerVerificationRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify an influencer profile (admin only).
    """
    service = InfluencerService(db)
    
    influencer = await service.update(
        UUID(influencer_id),
        InfluencerUpdate(verification_status=data.verification_status)
    )
    
    if not influencer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Influencer not found"
        )
    
    return influencer


@router.post("/{influencer_id}/social-accounts", response_model=SocialAccountResponse)
async def add_social_account(
    influencer_id: str,
    data: SocialAccountCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Add a social account to an influencer.
    """
    service = InfluencerService(db)
    
    try:
        account = await service.add_social_account(UUID(influencer_id), data)
        return account
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{influencer_id}/social-accounts/{account_id}", response_model=SocialAccountResponse)
async def update_social_account(
    influencer_id: str,
    account_id: str,
    data: SocialAccountUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update a social account.
    """
    service = InfluencerService(db)
    
    account = await service.update_social_account(
        UUID(influencer_id),
        UUID(account_id),
        data
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social account not found"
        )
    
    return account


@router.delete("/{influencer_id}/social-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_social_account(
    influencer_id: str,
    account_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a social account.
    """
    service = InfluencerService(db)
    
    success = await service.delete_social_account(UUID(influencer_id), UUID(account_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social account not found"
        )


@router.get("/{influencer_id}/content", response_model=dict)
async def get_influencer_content(
    influencer_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    content_type: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get content items for an influencer.
    """
    from app.services.content_service import ContentService
    
    service = ContentService(db)
    result = await service.get_by_influencer(
        UUID(influencer_id),
        page=page,
        page_size=page_size,
        content_type=content_type
    )
    
    return {
        "items": result["items"],
        "total": result["total"],
        "page": page,
        "page_size": page_size
    }


@router.get("/{influencer_id}/rank-history", response_model=List[dict])
async def get_influencer_rank_history(
    influencer_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get ranking history for an influencer.
    """
    from app.services.ranking_service import RankingService
    
    service = RankingService(db)
    history = await service.get_influencer_history(UUID(influencer_id), days)
    
    return history


@router.post("/bulk-import", response_model=dict)
async def bulk_import_influencers(
    data: InfluencerBulkImportRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Bulk import influencers (admin only).
    """
    service = InfluencerService(db)
    
    result = await service.bulk_import(
        data.influencers,
        created_by=UUID(current_user["id"])
    )
    
    return result


@router.get("/{influencer_id}/similar", response_model=List[dict])
async def get_similar_influencers(
    influencer_id: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get similar influencers.
    """
    service = InfluencerService(db)
    
    similar = await service.get_similar(UUID(influencer_id), limit)
    
    return similar
