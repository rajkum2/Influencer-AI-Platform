"""
Watchlists endpoints.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_active_user
from app.db.base import get_db
from app.schemas.watchlist import (
    WatchlistAddMember,
    WatchlistCreate,
    WatchlistResponse,
    WatchlistUpdate,
)
from app.services.watchlist_service import WatchlistService

router = APIRouter()


@router.get("", response_model=dict)
async def list_watchlists(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List user's watchlists.
    """
    service = WatchlistService(db)
    watchlists = await service.get_user_watchlists(UUID(current_user["id"]))
    
    return {"watchlists": watchlists, "total": len(watchlists)}


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    data: WatchlistCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new watchlist.
    """
    service = WatchlistService(db)
    
    watchlist = await service.create(data, owner_id=UUID(current_user["id"]))
    return watchlist


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get watchlist details.
    """
    service = WatchlistService(db)
    watchlist = await service.get_by_id(UUID(watchlist_id))
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )
    
    # Check access
    if not await service.can_access(UUID(watchlist_id), UUID(current_user["id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return watchlist


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: str,
    data: WatchlistUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update watchlist.
    """
    service = WatchlistService(db)
    
    # Check ownership
    if not await service.is_owner(UUID(watchlist_id), UUID(current_user["id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can update watchlist"
        )
    
    watchlist = await service.update(UUID(watchlist_id), data)
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )
    
    return watchlist


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete watchlist.
    """
    service = WatchlistService(db)
    
    # Check ownership
    if not await service.is_owner(UUID(watchlist_id), UUID(current_user["id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can delete watchlist"
        )
    
    success = await service.delete(UUID(watchlist_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )


@router.post("/{watchlist_id}/members", response_model=dict)
async def add_watchlist_member(
    watchlist_id: str,
    data: WatchlistAddMember,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Add influencer to watchlist.
    """
    service = WatchlistService(db)
    
    # Check access
    if not await service.can_edit(UUID(watchlist_id), UUID(current_user["id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    member = await service.add_member(
        UUID(watchlist_id),
        UUID(data.influencer_id),
        added_by=UUID(current_user["id"]),
        notes=data.notes,
        priority=data.priority,
        tags=data.tags
    )
    
    return member


@router.delete("/{watchlist_id}/members/{influencer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_watchlist_member(
    watchlist_id: str,
    influencer_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Remove influencer from watchlist.
    """
    service = WatchlistService(db)
    
    # Check access
    if not await service.can_edit(UUID(watchlist_id), UUID(current_user["id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    success = await service.remove_member(UUID(watchlist_id), UUID(influencer_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
