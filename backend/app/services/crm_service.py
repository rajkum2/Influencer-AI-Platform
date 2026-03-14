"""
CRM service for business logic.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.logging import get_logger
from app.models.crm import InfluencerRelationship, Interaction
from app.models.influencer import Influencer
from app.schemas.crm import (
    InteractionCreate,
    RelationshipCreate,
    RelationshipListParams,
    RelationshipUpdate,
)

logger = get_logger(__name__)


class CRMService:
    """Service for CRM operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_relationships(
        self,
        user_id: UUID,
        params: RelationshipListParams
    ) -> dict:
        """Get relationships for a user."""
        
        query = select(InfluencerRelationship).where(
            InfluencerRelationship.owner_id == user_id
        )
        
        # Apply filters
        if params.stage:
            query = query.where(InfluencerRelationship.stage == params.stage)
        
        if params.opportunity_type:
            query = query.where(
                InfluencerRelationship.opportunity_type.contains([params.opportunity_type])
            )
        
        if params.source:
            query = query.where(InfluencerRelationship.source == params.source)
        
        if params.needs_follow_up:
            query = query.where(
                InfluencerRelationship.next_follow_up_at.isnot(None)
            )
        
        if params.follow_up_overdue:
            query = query.where(
                and_(
                    InfluencerRelationship.next_follow_up_at < datetime.utcnow(),
                    InfluencerRelationship.follow_up_reminder_sent == False
                )
            )
        
        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply sorting
        sort_field = params.sort_by or "updated_at"
        sort_column = getattr(InfluencerRelationship, sort_field, InfluencerRelationship.updated_at)
        
        if params.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Pagination
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)
        
        # Eager load
        query = query.options(
            joinedload(InfluencerRelationship.influencer),
            selectinload(InfluencerRelationship.interactions)
        )
        
        result = await self.db.execute(query)
        relationships = result.scalars().all()
        
        return {
            "items": relationships,
            "total": total,
            "page": params.page,
            "page_size": params.page_size
        }
    
    async def get_relationship(
        self,
        relationship_id: UUID
    ) -> Optional[InfluencerRelationship]:
        """Get relationship by ID."""
        
        query = select(InfluencerRelationship).where(
            InfluencerRelationship.id == relationship_id
        ).options(
            joinedload(InfluencerRelationship.influencer),
            selectinload(InfluencerRelationship.interactions)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_relationship(
        self,
        data: RelationshipCreate,
        owner_id: UUID
    ) -> InfluencerRelationship:
        """Create a relationship."""
        
        # Check if relationship already exists
        existing = await self.db.execute(
            select(InfluencerRelationship).where(
                and_(
                    InfluencerRelationship.influencer_id == UUID(data.influencer_id),
                    InfluencerRelationship.owner_id == owner_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Relationship already exists for this influencer")
        
        relationship = InfluencerRelationship(
            influencer_id=UUID(data.influencer_id),
            owner_id=owner_id,
            stage=data.stage,
            notes=data.notes,
            opportunity_type=data.opportunity_type or [],
            estimated_value=data.estimated_value,
            currency=data.currency,
            tags=data.tags or [],
            source=data.source
        )
        
        self.db.add(relationship)
        await self.db.commit()
        await self.db.refresh(relationship)
        
        logger.info(
            "Relationship created",
            relationship_id=str(relationship.id),
            influencer_id=data.influencer_id,
            owner_id=str(owner_id)
        )
        
        return relationship
    
    async def update_relationship(
        self,
        relationship_id: UUID,
        data: RelationshipUpdate
    ) -> Optional[InfluencerRelationship]:
        """Update a relationship."""
        
        relationship = await self.get_relationship(relationship_id)
        if not relationship:
            return None
        
        old_stage = relationship.stage
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(relationship, field, value)
        
        # Update timestamps
        if data.stage == "partnered":
            relationship.actual_close_date = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(relationship)
        
        logger.info(
            "Relationship updated",
            relationship_id=str(relationship_id),
            old_stage=old_stage,
            new_stage=relationship.stage
        )
        
        return relationship
    
    async def delete_relationship(self, relationship_id: UUID) -> bool:
        """Delete a relationship."""
        
        relationship = await self.get_relationship(relationship_id)
        if not relationship:
            return False
        
        await self.db.delete(relationship)
        await self.db.commit()
        
        return True
    
    async def get_interactions(
        self,
        relationship_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """Get interactions for a relationship."""
        
        query = select(Interaction).where(
            Interaction.relationship_id == relationship_id
        ).order_by(desc(Interaction.occurred_at))
        
        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        interactions = result.scalars().all()
        
        return {
            "items": interactions,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def create_interaction(
        self,
        data: InteractionCreate,
        created_by: UUID
    ) -> Interaction:
        """Create an interaction."""
        
        interaction = Interaction(
            relationship_id=UUID(data.relationship_id),
            interaction_type=data.interaction_type,
            direction=data.direction,
            subject=data.subject,
            content=data.content,
            outcome=data.outcome,
            next_steps=data.next_steps,
            occurred_at=data.occurred_at or datetime.utcnow(),
            duration_minutes=data.duration_minutes,
            created_by=created_by,
            attachments=data.attachments or []
        )
        
        self.db.add(interaction)
        
        # Update relationship last_contacted_at
        relationship = await self.get_relationship(UUID(data.relationship_id))
        if relationship:
            relationship.last_contacted_at = interaction.occurred_at
        
        await self.db.commit()
        await self.db.refresh(interaction)
        
        return interaction
    
    async def get_pipeline_stats(self, user_id: UUID) -> dict:
        """Get pipeline statistics."""
        
        query = select(InfluencerRelationship).where(
            InfluencerRelationship.owner_id == user_id
        )
        
        result = await self.db.execute(query)
        relationships = result.scalars().all()
        
        # Calculate stats
        by_stage = {}
        total_value = 0
        weighted_value = 0
        closed_won = 0
        closed_lost = 0
        
        for rel in relationships:
            stage = rel.stage
            by_stage[stage] = by_stage.get(stage, 0) + 1
            
            if rel.estimated_value:
                total_value += rel.estimated_value
                probability = (rel.probability or 50) / 100
                weighted_value += rel.estimated_value * probability
            
            if stage == "partnered":
                closed_won += 1
            elif stage == "declined":
                closed_lost += 1
        
        total = len(relationships)
        open_deals = total - closed_won - closed_lost
        
        conversion_rate = None
        if closed_won + closed_lost > 0:
            conversion_rate = closed_won / (closed_won + closed_lost)
        
        avg_deal_size = None
        if closed_won > 0:
            won_value = sum(
                r.estimated_value for r in relationships
                if r.stage == "partnered" and r.estimated_value
            )
            avg_deal_size = won_value / closed_won
        
        return {
            "total_relationships": total,
            "by_stage": by_stage,
            "total_value": total_value,
            "weighted_value": weighted_value,
            "avg_deal_size": avg_deal_size,
            "conversion_rate": conversion_rate
        }
