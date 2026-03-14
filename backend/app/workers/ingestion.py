"""
Content ingestion workers.
"""

from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import ConnectorError
from app.connectors.github import GitHubConnector
from app.connectors.youtube import YouTubeConnector
from app.core.config import settings
from app.core.logging import get_logger
from app.db.base import SessionLocal
from app.models.content import ContentItem
from app.models.influencer import SocialAccount
from app.models.system import APIUsage
from app.workers.celery_app import celery_app

logger = get_logger(__name__)

# Connector registry
CONNECTORS = {
    "youtube": YouTubeConnector,
    "github": GitHubConnector,
}


async def get_db_session() -> AsyncSession:
    """Get database session for workers."""
    async with SessionLocal() as session:
        return session


@celery_app.task(bind=True, max_retries=3)
def sync_all_youtube_channels(self) -> dict:
    """Sync all YouTube channels."""
    import asyncio
    return asyncio.run(_sync_all_youtube_channels())


async def _sync_all_youtube_channels() -> dict:
    """Async implementation of YouTube channel sync."""
    
    async with SessionLocal() as db:
        # Get all YouTube accounts
        from sqlalchemy import select
        result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.platform == "youtube"
            )
        )
        accounts = result.scalars().all()
        
        synced = 0
        failed = 0
        
        connector = YouTubeConnector(settings.youtube_api_key)
        
        for account in accounts:
            try:
                await _sync_youtube_account(db, account, connector)
                synced += 1
            except Exception as e:
                logger.error(
                    "Failed to sync YouTube account",
                    account_id=str(account.id),
                    error=str(e)
                )
                failed += 1
        
        return {
            "total": len(accounts),
            "synced": synced,
            "failed": failed
        }


async def _sync_youtube_account(
    db: AsyncSession,
    account: SocialAccount,
    connector: YouTubeConnector
) -> dict:
    """Sync a single YouTube account."""
    
    # Get channel info
    channel_info = await connector.get_channel_info(account.platform_user_id)
    
    # Update account metrics
    account.followers_count = channel_info.get("subscriber_count")
    account.post_count = channel_info.get("video_count")
    account.last_synced_at = datetime.utcnow()
    account.sync_status = "success"
    
    # Get recent videos
    videos = await connector.get_channel_videos(
        account.platform_user_id,
        max_results=50
    )
    
    new_content = 0
    
    for video in videos:
        # Check if already exists
        from sqlalchemy import select, and_
        existing = await db.execute(
            select(ContentItem).where(
                and_(
                    ContentItem.platform == "youtube",
                    ContentItem.external_id == video["id"]
                )
            )
        )
        
        if existing.scalar_one_or_none():
            continue
        
        # Create content item
        content = ContentItem(
            influencer_id=account.influencer_id,
            social_account_id=account.id,
            platform="youtube",
            content_type="video",
            external_id=video["id"],
            original_url=f"https://youtube.com/watch?v={video['id']}",
            title=video.get("title"),
            body_text=video.get("description"),
            thumbnail_url=video.get("thumbnail_url"),
            duration_seconds=video.get("duration_seconds"),
            published_at=video.get("published_at"),
            views=video.get("view_count"),
            likes=video.get("like_count"),
            processing_status="pending"
        )
        
        db.add(content)
        new_content += 1
    
    await db.commit()
    
    logger.info(
        "YouTube account synced",
        account_id=str(account.id),
        new_content=new_content
    )
    
    return {"new_content": new_content}


@celery_app.task(bind=True, max_retries=3)
def sync_all_github_accounts(self) -> dict:
    """Sync all GitHub accounts."""
    import asyncio
    return asyncio.run(_sync_all_github_accounts())


async def _sync_all_github_accounts() -> dict:
    """Async implementation of GitHub account sync."""
    
    async with SessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.platform == "github"
            )
        )
        accounts = result.scalars().all()
        
        synced = 0
        failed = 0
        
        connector = GitHubConnector(settings.github_token)
        
        for account in accounts:
            try:
                await _sync_github_account(db, account, connector)
                synced += 1
            except Exception as e:
                logger.error(
                    "Failed to sync GitHub account",
                    account_id=str(account.id),
                    error=str(e)
                )
                failed += 1
        
        return {
            "total": len(accounts),
            "synced": synced,
            "failed": failed
        }


async def _sync_github_account(
    db: AsyncSession,
    account: SocialAccount,
    connector: GitHubConnector
) -> dict:
    """Sync a single GitHub account."""
    
    # Get user info
    user_info = await connector.get_user_info(account.handle)
    
    # Update account metrics
    account.followers_count = user_info.get("followers")
    account.following_count = user_info.get("following")
    account.last_synced_at = datetime.utcnow()
    account.sync_status = "success"
    
    # Get recent repos/activity
    repos = await connector.get_user_repos(account.handle, max_results=30)
    
    new_content = 0
    
    for repo in repos:
        from sqlalchemy import select, and_
        existing = await db.execute(
            select(ContentItem).where(
                and_(
                    ContentItem.platform == "github",
                    ContentItem.external_id == str(repo["id"])
                )
            )
        )
        
        if existing.scalar_one_or_none():
            continue
        
        content = ContentItem(
            influencer_id=account.influencer_id,
            social_account_id=account.id,
            platform="github",
            content_type="repo",
            external_id=str(repo["id"]),
            original_url=repo["html_url"],
            title=repo["name"],
            body_text=repo.get("description"),
            published_at=repo.get("created_at"),
            views=repo.get("watchers_count"),
            likes=repo.get("stargazers_count"),
            processing_status="pending"
        )
        
        db.add(content)
        new_content += 1
    
    await db.commit()
    
    logger.info(
        "GitHub account synced",
        account_id=str(account.id),
        new_content=new_content
    )
    
    return {"new_content": new_content}


def process_account_sync(account_id: str, platform: str) -> dict:
    """Process account sync request."""
    import asyncio
    return asyncio.run(_process_account_sync(account_id, platform))


async def _process_account_sync(account_id: str, platform: str) -> dict:
    """Async implementation of account sync."""
    
    async with SessionLocal() as db:
        account = await db.get(SocialAccount, UUID(account_id))
        
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        if platform == "youtube":
            connector = YouTubeConnector(settings.youtube_api_key)
            return await _sync_youtube_account(db, account, connector)
        elif platform == "github":
            connector = GitHubConnector(settings.github_token)
            return await _sync_github_account(db, account, connector)
        else:
            raise ValueError(f"Unsupported platform: {platform}")


from datetime import datetime
