"""
CRM endpoints.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_active_user
from app.db.base import get_db
from app.schemas.crm import (
    InteractionCreate,
    InteractionResponse,
    InteractionUpdate,
    PipelineStatsResponse,
    RelationshipCreate,
    RelationshipListParams,
    RelationshipResponse,
    RelationshipStageUpdate,
    RelationshipUpdate,
)
from app.services.crm_service import CRMService

router = APIRouter()


@router.get("/relationships", response_model=dict)
async def list_relationships(
    params: RelationshipListParams = Depends(),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List CRM relationships.
    """
    service = CRMService(db)
    result = await service.get_relationships(
        user_id=UUID(current_user["id"]),
        params=params
    )
    
    return result


@router.post("/relationships", response_model=RelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    data: RelationshipCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a relationship.
    """
    service = CRMService(db)
    
    try:
        relationship = await service.create_relationship(
            data,
            owner_id=UUID(current_user["id"])
        )
        return relationship
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/relationships/{relationship_id}", response_model=RelationshipResponse)
async def get_relationship(
    relationship_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get relationship details.
    """
    service = CRMService(db)
    relationship = await service.get_relationship(UUID(relationship_id))
    
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found"
        )
    
    # Check ownership
    if str(relationship.owner_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return relationship


@router.put("/relationships/{relationship_id}", response_model=RelationshipResponse)
async def update_relationship(
    relationship_id: str,
    data: RelationshipUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update relationship.
    """
    service = CRMService(db)
    
    # Check ownership
    relationship = await service.get_relationship(UUID(relationship_id))
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found"
        )
    
    if str(relationship.owner_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    updated = await service.update_relationship(UUID(relationship_id), data)
    return updated


@router.patch("/relationships/{relationship_id}/stage", response_model=RelationshipResponse)
async def update_relationship_stage(
    relationship_id: str,
    data: RelationshipStageUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update relationship stage.
    """
    service = CRMService(db)
    
    relationship = await service.get_relationship(UUID(relationship_id))
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found"
        )
    
    if str(relationship.owner_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    updated = await service.update_relationship(
        UUID(relationship_id),
        RelationshipUpdate(stage=data.stage, notes=data.notes)
    )
    return updated


@router.delete("/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    relationship_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete relationship.
    """
    service = CRMService(db)
    
    relationship = await service.get_relationship(UUID(relationship_id))
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found"
        )
    
    if str(relationship.owner_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await service.delete_relationship(UUID(relationship_id))


@router.get("/relationships/{relationship_id}/interactions", response_model=dict)
async def list_interactions(
    relationship_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List interactions for a relationship.
    """
    service = CRMService(db)
    
    relationship = await service.get_relationship(UUID(relationship_id))
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found"
        )
    
    if str(relationship.owner_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    interactions = await service.get_interactions(
        UUID(relationship_id),
        page=page,
        page_size=page_size
    )
    
    return interactions


@router.post("/relationships/{relationship_id}/interactions", response_model=InteractionResponse)
async def create_interaction(
    relationship_id: str,
    data: InteractionCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create an interaction.
    """
    service = CRMService(db)
    
    relationship = await service.get_relationship(UUID(relationship_id))
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found"
        )
    
    if str(relationship.owner_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    interaction = await service.create_interaction(
        data,
        created_by=UUID(current_user["id"])
    )
    return interaction


@router.get("/pipeline-stats", response_model=PipelineStatsResponse)
async def get_pipeline_stats(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get pipeline statistics.
    """
    service = CRMService(db)
    stats = await service.get_pipeline_stats(UUID(current_user["id"]))
    
    return stats
