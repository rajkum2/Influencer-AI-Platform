"""
Technology service for business logic.
"""

from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.technology import Technology, InfluencerTechnology, ContentTechnology
from app.schemas.technology import TechnologyCreate, TechnologyListParams, TechnologyUpdate

logger = get_logger(__name__)


class TechnologyService:
    """Service for technology/taxonomy operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_technologies(self, params: TechnologyListParams) -> dict:
        """Get technologies with filtering."""
        
        query = select(Technology)
        
        if params.is_active is not None:
            query = query.where(Technology.is_active == params.is_active)
        
        if params.parent_id:
            query = query.where(Technology.parent_id == UUID(params.parent_id))
        else:
            # Default to top-level only
            query = query.where(Technology.parent_id.is_(None))
        
        if params.has_content:
            query = query.where(Technology.content_count > 0)
        
        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                Technology.name.ilike(search_term) |
                Technology.description.ilike(search_term)
            )
        
        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Order by display_order, then name
        query = query.order_by(Technology.display_order, Technology.name)
        
        # Pagination
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total
        }
    
    async def get_by_id(self, technology_id: UUID) -> Optional[Technology]:
        """Get technology by ID."""
        query = select(Technology).where(Technology.id == technology_id).options(
            selectinload(Technology.children)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug: str) -> Optional[Technology]:
        """Get technology by slug."""
        query = select(Technology).where(Technology.slug == slug)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, data: TechnologyCreate) -> Technology:
        """Create a technology."""
        
        # Generate slug if not provided
        from slugify import slugify
        slug = data.slug or slugify(data.name)
        
        # Check if slug exists
        existing = await self.get_by_slug(slug)
        if existing:
            raise ValueError(f"Technology with slug '{slug}' already exists")
        
        tech = Technology(
            name=data.name,
            slug=slug,
            description=data.description,
            parent_id=UUID(data.parent_id) if data.parent_id else None,
            keywords=data.keywords or [],
            color=data.color,
            icon=data.icon,
            is_active=True
        )
        
        self.db.add(tech)
        await self.db.commit()
        await self.db.refresh(tech)
        
        logger.info("Technology created", technology_id=str(tech.id), name=tech.name)
        
        return tech
    
    async def update(
        self,
        technology_id: UUID,
        data: TechnologyUpdate
    ) -> Optional[Technology]:
        """Update a technology."""
        
        tech = await self.get_by_id(technology_id)
        if not tech:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(tech, field, value)
        
        await self.db.commit()
        await self.db.refresh(tech)
        
        return tech
    
    async def delete(self, technology_id: UUID) -> bool:
        """Delete a technology."""
        
        tech = await self.get_by_id(technology_id)
        if not tech:
            return False
        
        await self.db.delete(tech)
        await self.db.commit()
        
        return True
    
    async def get_tree(self) -> List[Technology]:
        """Get technology tree structure."""
        
        query = select(Technology).where(
            and_(
                Technology.is_active == True,
                Technology.parent_id.is_(None)
            )
        ).order_by(Technology.display_order, Technology.name).options(
            selectinload(Technology.children)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_influencers(
        self,
        technology_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """Get influencers for a technology."""
        
        from app.models.influencer import Influencer
        
        query = select(Influencer, InfluencerTechnology.relevance_score).join(
            InfluencerTechnology
        ).where(
            and_(
                InfluencerTechnology.technology_id == technology_id,
                Influencer.is_active == True
            )
        )
        
        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Order by relevance
        query = query.order_by(InfluencerTechnology.relevance_score.desc())
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        items = [
            {
                "influencer_id": str(row.Influencer.id),
                "influencer_name": row.Influencer.full_name,
                "profile_image_url": row.Influencer.profile_image_url,
                "relevance_score": row.relevance_score,
                "content_count": await self._get_influencer_content_count(
                    row.Influencer.id, technology_id
                )
            }
            for row in rows
        ]
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def _get_influencer_content_count(
        self,
        influencer_id: UUID,
        technology_id: UUID
    ) -> int:
        """Get content count for influencer in technology."""
        
        query = select(func.count()).select_from(ContentTechnology).join(
            "content_item"
        ).where(
            and_(
                ContentTechnology.technology_id == technology_id,
                ContentTechnology.content_item.has(influencer_id=influencer_id)
            )
        )
        
        return await self.db.scalar(query) or 0
    
    async def get_content(
        self,
        technology_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """Get content for a technology."""
        
        from app.models.content import ContentItem
        
        query = select(ContentItem, ContentTechnology.relevance_score).join(
            ContentTechnology
        ).where(
            ContentTechnology.technology_id == technology_id
        )
        
        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Order by published date
        query = query.order_by(ContentItem.published_at.desc())
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        items = [
            {
                "content_id": str(row.ContentItem.id),
                "title": row.ContentItem.title,
                "platform": row.ContentItem.platform,
                "published_at": row.ContentItem.published_at,
                "relevance_score": row.relevance_score
            }
            for row in rows
        ]
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
