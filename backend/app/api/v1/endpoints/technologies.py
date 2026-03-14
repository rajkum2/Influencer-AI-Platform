"""
Technology endpoints.
"""

from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_active_user, require_admin
from app.db.base import get_db
from app.schemas.technology import (
    TechnologyCreate,
    TechnologyListParams,
    TechnologyResponse,
    TechnologyUpdate,
)
from app.services.technology_service import TechnologyService

router = APIRouter()


@router.get("", response_model=dict)
async def list_technologies(
    params: TechnologyListParams = Depends(),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List technologies/taxonomy.
    """
    service = TechnologyService(db)
    result = await service.get_technologies(params)
    
    return {
        "items": result["items"],
        "total": result["total"],
        "page": params.page,
        "page_size": params.page_size
    }


@router.get("/tree", response_model=dict)
async def get_technology_tree(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get technology tree structure.
    """
    service = TechnologyService(db)
    tree = await service.get_tree()
    
    return {"technologies": tree}


@router.post("", response_model=TechnologyResponse, status_code=status.HTTP_201_CREATED)
async def create_technology(
    data: TechnologyCreate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a technology (admin only).
    """
    service = TechnologyService(db)
    
    try:
        tech = await service.create(data)
        return tech
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{technology_id}", response_model=TechnologyResponse)
async def get_technology(
    technology_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get technology details.
    """
    service = TechnologyService(db)
    tech = await service.get_by_id(UUID(technology_id))
    
    if not tech:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technology not found"
        )
    
    return tech


@router.put("/{technology_id}", response_model=TechnologyResponse)
async def update_technology(
    technology_id: str,
    data: TechnologyUpdate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update technology (admin only).
    """
    service = TechnologyService(db)
    
    tech = await service.update(UUID(technology_id), data)
    if not tech:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technology not found"
        )
    
    return tech


@router.delete("/{technology_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_technology(
    technology_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete technology (admin only).
    """
    service = TechnologyService(db)
    
    success = await service.delete(UUID(technology_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technology not found"
        )


@router.get("/{technology_id}/influencers", response_model=dict)
async def get_technology_influencers(
    technology_id: str,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get influencers for a technology.
    """
    service = TechnologyService(db)
    result = await service.get_influencers(UUID(technology_id), page, page_size)
    
    return result


@router.get("/{technology_id}/content", response_model=dict)
async def get_technology_content(
    technology_id: str,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get content for a technology.
    """
    service = TechnologyService(db)
    result = await service.get_content(UUID(technology_id), page, page_size)
    
    return result
