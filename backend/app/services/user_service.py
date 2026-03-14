"""
User service for business logic.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import get_password_hash, verify_password
from app.models.user import Team, User
from app.schemas.user import TeamCreate, UserCreate, UserUpdate

logger = get_logger(__name__)


class UserService:
    """Service for user operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user."""
        user = await self.get_by_email(email)
        if not user:
            return None
        
        if not user.password_hash:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def create(self, data: UserCreate) -> User:
        """Create a new user."""
        
        # Check if email exists
        existing = await self.get_by_email(data.email)
        if existing:
            raise ValueError(f"User with email '{data.email}' already exists")
        
        user = User(
            email=data.email.lower(),
            password_hash=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            role=data.role,
            team_id=data.team_id,
            is_active=True
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info("User created", user_id=str(user.id), email=user.email)
        
        return user
    
    async def update(self, user_id: UUID, data: UserUpdate) -> Optional[User]:
        """Update a user."""
        
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def update_last_login(self, user_id: UUID) -> None:
        """Update last login timestamp."""
        
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            await self.db.commit()
    
    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password."""
        
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        if not verify_password(current_password, user.password_hash):
            return False
        
        user.password_hash = get_password_hash(new_password)
        await self.db.commit()
        
        return True


class TeamService:
    """Service for team operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, team_id: UUID) -> Optional[Team]:
        """Get team by ID."""
        result = await self.db.execute(
            select(Team).where(Team.id == team_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug: str) -> Optional[Team]:
        """Get team by slug."""
        result = await self.db.execute(
            select(Team).where(Team.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def create(self, data: TeamCreate) -> Team:
        """Create a new team."""
        
        from slugify import slugify
        
        slug = data.slug or slugify(data.name)
        
        # Check if slug exists
        existing = await self.get_by_slug(slug)
        if existing:
            raise ValueError(f"Team with slug '{slug}' already exists")
        
        team = Team(
            name=data.name,
            slug=slug,
            plan="free",
            max_influencers=100,
            max_team_members=3,
            max_watchlists=10
        )
        
        self.db.add(team)
        await self.db.commit()
        await self.db.refresh(team)
        
        logger.info("Team created", team_id=str(team.id), name=team.name)
        
        return team
    
    async def update(self, team_id: UUID, data: dict) -> Optional[Team]:
        """Update a team."""
        
        team = await self.get_by_id(team_id)
        if not team:
            return None
        
        for field, value in data.items():
            if hasattr(team, field) and value is not None:
                setattr(team, field, value)
        
        await self.db.commit()
        await self.db.refresh(team)
        
        return team
