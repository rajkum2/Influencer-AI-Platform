"""
Influencer service for business logic.
"""

from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.logging import get_logger
from app.models.influencer import Influencer, SocialAccount
from app.models.technology import InfluencerTechnology
from app.schemas.influencer import (
    InfluencerCreate,
    InfluencerListParams,
    InfluencerUpdate,
    SocialAccountCreate,
    SocialAccountUpdate,
)

logger = get_logger(__name__)


class InfluencerService:
    """Service for influencer operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_influencers(self, params: InfluencerListParams) -> dict:
        """Get influencers with filtering and pagination."""
        
        # Build base query
        query = select(Influencer).where(Influencer.is_active == True)
        
        # Apply filters
        if params.technology_id:
            query = query.join(
                InfluencerTechnology,
                InfluencerTechnology.influencer_id == Influencer.id
            ).where(InfluencerTechnology.technology_id == UUID(params.technology_id))
        
        if params.country_code:
            query = query.where(Influencer.country_code == params.country_code.upper())
        
        if params.region:
            query = query.where(Influencer.region.ilike(f"%{params.region}%"))
        
        if params.city:
            query = query.where(Influencer.city.ilike(f"%{params.city}%"))
        
        if params.role_type:
            query = query.where(Influencer.role_type == params.role_type)
        
        if params.company:
            query = query.where(Influencer.company.ilike(f"%{params.company}%"))
        
        if params.verification_status:
            query = query.where(
                Influencer.verification_status == params.verification_status
            )
        
        if params.is_featured is not None:
            query = query.where(Influencer.is_featured == params.is_featured)
        
        if params.platform:
            query = query.join(SocialAccount).where(
                SocialAccount.platform == params.platform
            )
        
        if params.min_followers is not None:
            query = query.where(Influencer.total_followers >= params.min_followers)
        
        if params.max_followers is not None:
            query = query.where(Influencer.total_followers <= params.max_followers)
        
        if params.min_content_count is not None:
            query = query.where(
                Influencer.content_count >= params.min_content_count
            )
        
        if params.active_since_days:
            from datetime import datetime, timedelta
            cutoff = datetime.utcnow() - timedelta(days=params.active_since_days)
            query = query.where(Influencer.last_content_at >= cutoff)
        
        # Search
        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                or_(
                    Influencer.full_name.ilike(search_term),
                    Influencer.display_name.ilike(search_term),
                    Influencer.headline.ilike(search_term),
                    Influencer.bio.ilike(search_term),
                    Influencer.company.ilike(search_term)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply sorting
        sort_field = params.sort_by or "overall_rank"
        sort_column = getattr(Influencer, sort_field, Influencer.created_at)
        
        if params.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)
        
        # Eager load relationships
        query = query.options(
            selectinload(Influencer.social_accounts),
            selectinload(Influencer.technologies).joinedload(
                InfluencerTechnology.technology
            )
        )
        
        # Execute
        result = await self.db.execute(query)
        influencers = result.scalars().all()
        
        return {
            "items": influencers,
            "total": total
        }
    
    async def get_by_id(self, influencer_id: UUID) -> Optional[Influencer]:
        """Get influencer by ID with full details."""
        query = select(Influencer).where(
            and_(Influencer.id == influencer_id, Influencer.is_active == True)
        ).options(
            selectinload(Influencer.social_accounts),
            selectinload(Influencer.technologies).joinedload(
                InfluencerTechnology.technology
            ),
            selectinload(Influencer.rank_snapshots),
            selectinload(Influencer.relationships)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(
        self,
        data: InfluencerCreate,
        created_by: Optional[UUID] = None
    ) -> Influencer:
        """Create a new influencer."""
        
        # Check if influencer with same name exists
        existing = await self.db.execute(
            select(Influencer).where(
                func.lower(Influencer.full_name) == data.full_name.lower()
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Influencer with name '{data.full_name}' already exists")
        
        # Create influencer
        influencer = Influencer(
            full_name=data.full_name,
            display_name=data.display_name,
            headline=data.headline,
            bio=data.bio,
            country_code=data.country_code.upper() if data.country_code else None,
            region=data.region,
            city=data.city,
            timezone=data.timezone,
            company=data.company,
            role_type=data.role_type,
            website_url=str(data.website_url) if data.website_url else None,
            email_public=data.email_public,
            created_by=created_by,
            verification_status="pending"
        )
        
        self.db.add(influencer)
        await self.db.flush()  # Get the ID
        
        # Create social accounts
        if data.social_accounts:
            for account_data in data.social_accounts:
                account = SocialAccount(
                    influencer_id=influencer.id,
                    platform=account_data.platform,
                    handle=account_data.handle,
                    url=str(account_data.url),
                    platform_user_id=account_data.platform_user_id,
                    is_verified=account_data.is_verified,
                    account_type=account_data.account_type,
                    sync_status="pending"
                )
                self.db.add(account)
        
        # Add technologies
        if data.technology_ids:
            for tech_id in data.technology_ids:
                mapping = InfluencerTechnology(
                    influencer_id=influencer.id,
                    technology_id=UUID(tech_id),
                    detection_method="manual"
                )
                self.db.add(mapping)
        
        await self.db.commit()
        await self.db.refresh(influencer)
        
        logger.info(
            "Influencer created",
            influencer_id=str(influencer.id),
            name=influencer.full_name,
            created_by=str(created_by)
        )
        
        return influencer
    
    async def update(
        self,
        influencer_id: UUID,
        data: InfluencerUpdate
    ) -> Optional[Influencer]:
        """Update an influencer."""
        
        influencer = await self.get_by_id(influencer_id)
        if not influencer:
            return None
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                if field == "website_url" and value:
                    value = str(value)
                setattr(influencer, field, value)
        
        await self.db.commit()
        await self.db.refresh(influencer)
        
        logger.info(
            "Influencer updated",
            influencer_id=str(influencer_id)
        )
        
        return influencer
    
    async def delete(self, influencer_id: UUID) -> bool:
        """Soft delete an influencer."""
        
        influencer = await self.get_by_id(influencer_id)
        if not influencer:
            return False
        
        influencer.is_active = False
        await self.db.commit()
        
        logger.info(
            "Influencer deleted",
            influencer_id=str(influencer_id)
        )
        
        return True
    
    async def search(self, query: str, page: int, page_size: int) -> dict:
        """Search influencers."""
        
        # Use full-text search if available, otherwise fallback to ILIKE
        search_term = f"%{query}%"
        
        db_query = select(Influencer).where(
            and_(
                Influencer.is_active == True,
                or_(
                    Influencer.full_name.ilike(search_term),
                    Influencer.display_name.ilike(search_term),
                    Influencer.headline.ilike(search_term),
                    Influencer.bio.ilike(search_term),
                    Influencer.company.ilike(search_term)
                )
            )
        )
        
        # Get total
        count_query = select(func.count()).select_from(db_query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        db_query = db_query.offset(offset).limit(page_size)
        
        # Eager load
        db_query = db_query.options(
            selectinload(Influencer.social_accounts),
            selectinload(Influencer.technologies)
        )
        
        result = await self.db.execute(db_query)
        influencers = result.scalars().all()
        
        return {
            "items": influencers,
            "total": total
        }
    
    async def add_social_account(
        self,
        influencer_id: UUID,
        data: SocialAccountCreate
    ) -> SocialAccount:
        """Add a social account to an influencer."""
        
        # Check if account already exists
        existing = await self.db.execute(
            select(SocialAccount).where(
                and_(
                    SocialAccount.influencer_id == influencer_id,
                    SocialAccount.platform == data.platform
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(
                f"Influencer already has a {data.platform} account"
            )
        
        account = SocialAccount(
            influencer_id=influencer_id,
            platform=data.platform,
            handle=data.handle,
            url=str(data.url),
            platform_user_id=data.platform_user_id,
            is_verified=data.is_verified,
            account_type=data.account_type,
            sync_status="pending"
        )
        
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        
        return account
    
    async def update_social_account(
        self,
        influencer_id: UUID,
        account_id: UUID,
        data: SocialAccountUpdate
    ) -> Optional[SocialAccount]:
        """Update a social account."""
        
        result = await self.db.execute(
            select(SocialAccount).where(
                and_(
                    SocialAccount.id == account_id,
                    SocialAccount.influencer_id == influencer_id
                )
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                if field in ("url",) and value:
                    value = str(value)
                setattr(account, field, value)
        
        await self.db.commit()
        await self.db.refresh(account)
        
        return account
    
    async def delete_social_account(
        self,
        influencer_id: UUID,
        account_id: UUID
    ) -> bool:
        """Delete a social account."""
        
        result = await self.db.execute(
            select(SocialAccount).where(
                and_(
                    SocialAccount.id == account_id,
                    SocialAccount.influencer_id == influencer_id
                )
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            return False
        
        await self.db.delete(account)
        await self.db.commit()
        
        return True
    
    async def bulk_import(
        self,
        influencers_data: List[InfluencerCreate],
        created_by: Optional[UUID] = None
    ) -> dict:
        """Bulk import influencers."""
        
        created = []
        errors = []
        
        for i, data in enumerate(influencers_data):
            try:
                influencer = await self.create(data, created_by)
                created.append(str(influencer.id))
            except Exception as e:
                errors.append({
                    "index": i,
                    "name": data.full_name,
                    "error": str(e)
                })
        
        return {
            "success": len(created),
            "failed": len(errors),
            "created_ids": created,
            "errors": errors
        }
    
    async def get_similar(
        self,
        influencer_id: UUID,
        limit: int = 5
    ) -> List[dict]:
        """Get similar influencers."""
        
        # Get the influencer
        influencer = await self.get_by_id(influencer_id)
        if not influencer:
            return []
        
        # Get technology IDs
        tech_ids = [
            t.technology_id for t in influencer.technologies
            if t.relevance_score and t.relevance_score > 0.5
        ]
        
        if not tech_ids:
            # Fallback to same region/role
            query = select(Influencer).where(
                and_(
                    Influencer.id != influencer_id,
                    Influencer.is_active == True,
                    or_(
                        Influencer.region == influencer.region,
                        Influencer.role_type == influencer.role_type
                    )
                )
            ).limit(limit)
        else:
            # Find influencers with similar technologies
            query = select(Influencer).join(
                InfluencerTechnology
            ).where(
                and_(
                    Influencer.id != influencer_id,
                    Influencer.is_active == True,
                    InfluencerTechnology.technology_id.in_(tech_ids)
                )
            ).group_by(Influencer.id).order_by(
                func.count(InfluencerTechnology.technology_id).desc()
            ).limit(limit)
        
        result = await self.db.execute(query)
        similar = result.scalars().all()
        
        return [
            {
                "id": str(s.id),
                "full_name": s.full_name,
                "headline": s.headline,
                "profile_image_url": s.profile_image_url,
                "total_followers": s.total_followers,
                "overall_score": s.overall_score
            }
            for s in similar
        ]
