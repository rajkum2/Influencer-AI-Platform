"""
Content endpoints.
"""

from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_active_user, require_admin
from app.db.base import get_db
from app.schemas.content import (
    ContentClassificationRequest,
    ContentCreate,
    ContentListParams,
    ContentResponse,
    ContentUpdate,
)
from app.services.content_service import ContentService

router = APIRouter()


@router.get("", response_model=dict)
async def list_content(
    params: ContentListParams = Depends(),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List content items with filtering.
    """
    service = ContentService(db)
    result = await service.get_content_items(params)
    
    return {
        "items": result["items"],
        "total": result["total"],
        "page": params.page,
        "page_size": params.page_size,
        "pages": (result["total"] + params.page_size - 1) // params.page_size,
        "has_next": params.page * params.page_size < result["total"],
        "has_prev": params.page > 1
    }


@router.get("/feed", response_model=dict)
async def get_content_feed(
    days: int = Query(7, ge=1, le=30),
    technology_id: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get content feed for dashboard.
    """
    service = ContentService(db)
    feed = await service.get_feed(
        days=days,
        technology_id=UUID(technology_id) if technology_id else None
    )
    
    return feed


@router.post("", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    data: ContentCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a content item.
    """
    service = ContentService(db)
    
    try:
        content = await service.create(data)
        return content
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get content item details.
    """
    service = ContentService(db)
    content = await service.get_by_id(UUID(content_id))
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    return content


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    data: ContentUpdate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update content item (admin only).
    """
    service = ContentService(db)
    
    content = await service.update(UUID(content_id), data)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    return content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete content item (admin only).
    """
    service = ContentService(db)
    
    success = await service.delete(UUID(content_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )


@router.post("/classify")
async def classify_content(
    request: ContentClassificationRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Trigger content classification (admin only).
    """
    from app.workers.tasks import classify_content_batch
    
    # Queue classification task
    task = classify_content_batch.delay(request.content_ids)
    
    return {
        "job_id": task.id,
        "status": "queued",
        "message": f"Classification queued for {len(request.content_ids)} content items"
    }
