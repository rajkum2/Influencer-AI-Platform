"""
Content service for business logic.
"""

from datetime import datetime, timedelta
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.logging import get_logger
from app.models.content import ContentEngagement, ContentItem
from app.models.technology import ContentTechnology
from app.schemas.content import ContentCreate, ContentListParams, ContentUpdate

logger = get_logger(__name__)


class ContentService:
    """Service for content operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_content_items(self, params: ContentListParams) -> dict:
        """Get content items with filtering."""
        
        query = select(ContentItem)
        
        # Apply filters
        if params.influencer_id:
            query = query.where(
                ContentItem.influencer_id == UUID(params.influencer_id)
            )
        
        if params.platform:
            query = query.where(ContentItem.platform == params.platform)
        
        if params.content_type:
            query = query.where(ContentItem.content_type == params.content_type)
        
        if params.technology_id:
            query = query.join(
                ContentTechnology,
                ContentTechnology.content_id == ContentItem.id
            ).where(ContentTechnology.technology_id == UUID(params.technology_id))
        
        if params.language_code:
            query = query.where(
                ContentItem.language_code == params.language_code.lower()
            )
        
        if params.date_from:
            query = query.where(ContentItem.published_at >= params.date_from)
        
        if params.date_to:
            query = query.where(ContentItem.published_at <= params.date_to)
        
        if params.min_quality_score is not None:
            query = query.where(
                ContentItem.quality_score >= params.min_quality_score
            )
        
        if params.is_processed is not None:
            if params.is_processed:
                query = query.where(
                    ContentItem.processing_status == "completed"
                )
            else:
                query = query.where(
                    ContentItem.processing_status != "completed"
                )
        
        # Search
        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                or_(
                    ContentItem.title.ilike(search_term),
                    ContentItem.body_text.ilike(search_term)
                )
            )
        
        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply sorting
        sort_field = params.sort_by or "published_at"
        sort_column = getattr(ContentItem, sort_field, ContentItem.published_at)
        
        if params.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)
        
        # Eager load
        query = query.options(
            selectinload(ContentItem.technologies),
            joinedload(ContentItem.influencer)
        )
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total
        }
    
    async def get_by_id(self, content_id: UUID) -> Optional[ContentItem]:
        """Get content item by ID."""
        query = select(ContentItem).where(ContentItem.id == content_id).options(
            selectinload(ContentItem.technologies).joinedload(
                ContentTechnology.technology
            ),
            joinedload(ContentItem.influencer),
            joinedload(ContentItem.social_account)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_influencer(
        self,
        influencer_id: UUID,
        page: int = 1,
        page_size: int = 20,
        content_type: Optional[str] = None
    ) -> dict:
        """Get content items for an influencer."""
        
        query = select(ContentItem).where(
            ContentItem.influencer_id == influencer_id
        )
        
        if content_type:
            query = query.where(ContentItem.content_type == content_type)
        
        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Order by published date
        query = query.order_by(desc(ContentItem.published_at))
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        query = query.options(selectinload(ContentItem.technologies))
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total
        }
    
    async def create(self, data: ContentCreate) -> ContentItem:
        """Create a content item."""
        
        # Check for duplicates
        existing = await self.db.execute(
            select(ContentItem).where(
                and_(
                    ContentItem.platform == data.platform,
                    ContentItem.external_id == data.external_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(
                f"Content item already exists for {data.platform}:{data.external_id}"
            )
        
        content = ContentItem(
            influencer_id=UUID(data.influencer_id),
            social_account_id=UUID(data.social_account_id) if data.social_account_id else None,
            platform=data.platform,
            content_type=data.content_type,
            external_id=data.external_id,
            original_url=str(data.original_url),
            title=data.title,
            body_text=data.body_text,
            thumbnail_url=str(data.thumbnail_url) if data.thumbnail_url else None,
            duration_seconds=data.duration_seconds,
            published_at=data.published_at,
            language_code=data.language_code.lower() if data.language_code else None,
            processing_status="pending"
        )
        
        self.db.add(content)
        await self.db.flush()
        
        # Add technologies
        if data.technologies:
            for tech in data.technologies:
                mapping = ContentTechnology(
                    content_id=content.id,
                    technology_id=UUID(tech.technology_id),
                    relevance_score=tech.relevance_score,
                    confidence=tech.confidence,
                    detection_method="manual"
                )
                self.db.add(mapping)
        
        await self.db.commit()
        await self.db.refresh(content)
        
        logger.info(
            "Content item created",
            content_id=str(content.id),
            platform=content.platform,
            influencer_id=str(content.influencer_id)
        )
        
        return content
    
    async def update(
        self,
        content_id: UUID,
        data: ContentUpdate
    ) -> Optional[ContentItem]:
        """Update a content item."""
        
        content = await self.get_by_id(content_id)
        if not content:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(content, field, value)
        
        await self.db.commit()
        await self.db.refresh(content)
        
        return content
    
    async def delete(self, content_id: UUID) -> bool:
        """Delete a content item."""
        
        content = await self.get_by_id(content_id)
        if not content:
            return False
        
        await self.db.delete(content)
        await self.db.commit()
        
        return True
    
    async def get_feed(
        self,
        days: int = 7,
        technology_id: Optional[UUID] = None
    ) -> dict:
        """Get content feed for dashboard."""
        
        since = datetime.utcnow() - timedelta(days=days)
        
        query = select(ContentItem).where(
            ContentItem.published_at >= since
        )
        
        if technology_id:
            query = query.join(
                ContentTechnology,
                ContentTechnology.content_id == ContentItem.id
            ).where(ContentTechnology.technology_id == technology_id)
        
        query = query.order_by(desc(ContentItem.published_at)).limit(100)
        
        query = query.options(
            joinedload(ContentItem.influencer),
            selectinload(ContentItem.technologies)
        )
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        # Group by date
        date_grouped = {}
        for item in items:
            date_key = item.published_at.strftime("%Y-%m-%d") if item.published_at else "Unknown"
            if date_key not in date_grouped:
                date_grouped[date_key] = []
            date_grouped[date_key].append(item)
        
        # Count new today and this week
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        week_start = today_start - timedelta(days=today.weekday())
        
        new_today = sum(
            1 for item in items
            if item.published_at and item.published_at >= today_start
        )
        new_week = sum(
            1 for item in items
            if item.published_at and item.published_at >= week_start
        )
        
        return {
            "items": items,
            "date_grouped": date_grouped,
            "total_new_today": new_today,
            "total_new_week": new_week
        }
    
    async def get_pending_processing(self, limit: int = 100) -> List[ContentItem]:
        """Get content items pending AI processing."""
        
        query = select(ContentItem).where(
            ContentItem.processing_status == "pending"
        ).order_by(
            desc(ContentItem.published_at)
        ).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
