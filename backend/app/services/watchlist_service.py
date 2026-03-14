"""
Watchlist service for business logic.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.logging import get_logger
from app.models.influencer import Influencer
from app.models.watchlist import Watchlist, WatchlistMember
from app.schemas.watchlist import WatchlistCreate, WatchlistUpdate

logger = get_logger(__name__)


class WatchlistService:
    """Service for watchlist operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_watchlists(self, user_id: UUID) -> List[Watchlist]:
        """Get all watchlists accessible to a user."""
        
        query = select(Watchlist).where(
            or_(
                Watchlist.owner_id == user_id,
                Watchlist.is_shared == True,
                Watchlist.shared_with.contains([user_id])
            )
        ).options(
            selectinload(Watchlist.members)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_id(self, watchlist_id: UUID) -> Optional[Watchlist]:
        """Get watchlist by ID with full details."""
        
        query = select(Watchlist).where(Watchlist.id == watchlist_id).options(
            selectinload(Watchlist.members).joinedload(WatchlistMember.influencer)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(
        self,
        data: WatchlistCreate,
        owner_id: UUID
    ) -> Watchlist:
        """Create a new watchlist."""
        
        watchlist = Watchlist(
            name=data.name,
            description=data.description,
            owner_id=owner_id,
            team_id=UUID(data.team_id) if data.team_id else None,
            is_dynamic=data.is_dynamic,
            filter_criteria=data.filter_criteria or {},
            alert_config=data.alert_config or {},
            color=data.color,
            icon=data.icon
        )
        
        self.db.add(watchlist)
        await self.db.commit()
        await self.db.refresh(watchlist)
        
        logger.info(
            "Watchlist created",
            watchlist_id=str(watchlist.id),
            name=watchlist.name,
            owner_id=str(owner_id)
        )
        
        return watchlist
    
    async def update(
        self,
        watchlist_id: UUID,
        data: WatchlistUpdate
    ) -> Optional[Watchlist]:
        """Update a watchlist."""
        
        watchlist = await self.get_by_id(watchlist_id)
        if not watchlist:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(watchlist, field, value)
        
        await self.db.commit()
        await self.db.refresh(watchlist)
        
        return watchlist
    
    async def delete(self, watchlist_id: UUID) -> bool:
        """Delete a watchlist."""
        
        watchlist = await self.get_by_id(watchlist_id)
        if not watchlist:
            return False
        
        await self.db.delete(watchlist)
        await self.db.commit()
        
        return True
    
    async def add_member(
        self,
        watchlist_id: UUID,
        influencer_id: UUID,
        added_by: UUID,
        notes: Optional[str] = None,
        priority: str = "medium",
        tags: List[str] = None
    ) -> dict:
        """Add an influencer to a watchlist."""
        
        # Check if already exists
        existing = await self.db.execute(
            select(WatchlistMember).where(
                and_(
                    WatchlistMember.watchlist_id == watchlist_id,
                    WatchlistMember.influencer_id == influencer_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Influencer already in watchlist")
        
        member = WatchlistMember(
            watchlist_id=watchlist_id,
            influencer_id=influencer_id,
            added_by=added_by,
            notes=notes,
            priority=priority,
            tags=tags or []
        )
        
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        
        return {
            "id": str(member.id),
            "influencer_id": str(member.influencer_id),
            "added_at": member.added_at,
            "priority": member.priority
        }
    
    async def remove_member(
        self,
        watchlist_id: UUID,
        influencer_id: UUID
    ) -> bool:
        """Remove an influencer from a watchlist."""
        
        result = await self.db.execute(
            select(WatchlistMember).where(
                and_(
                    WatchlistMember.watchlist_id == watchlist_id,
                    WatchlistMember.influencer_id == influencer_id
                )
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            return False
        
        await self.db.delete(member)
        await self.db.commit()
        
        return True
    
    async def can_access(self, watchlist_id: UUID, user_id: UUID) -> bool:
        """Check if user can access watchlist."""
        
        watchlist = await self.db.get(Watchlist, watchlist_id)
        if not watchlist:
            return False
        
        if watchlist.owner_id == user_id:
            return True
        
        if watchlist.is_shared:
            return True
        
        if user_id in (watchlist.shared_with or []):
            return True
        
        return False
    
    async def can_edit(self, watchlist_id: UUID, user_id: UUID) -> bool:
        """Check if user can edit watchlist."""
        
        watchlist = await self.db.get(Watchlist, watchlist_id)
        if not watchlist:
            return False
        
        if watchlist.owner_id == user_id:
            return True
        
        # Check if user has edit permission
        if watchlist.is_shared and watchlist.share_permission in ("edit", "admin"):
            return True
        
        return False
    
    async def is_owner(self, watchlist_id: UUID, user_id: UUID) -> bool:
        """Check if user is the owner of watchlist."""
        
        watchlist = await self.db.get(Watchlist, watchlist_id)
        if not watchlist:
            return False
        
        return watchlist.owner_id == user_id
