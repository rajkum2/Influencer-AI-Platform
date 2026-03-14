"""
Main Celery tasks.
"""

from typing import List, Optional

from app.workers.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def classify_content_batch(self, content_ids: List[str]) -> dict:
    """
    Classify a batch of content items.
    
    Args:
        content_ids: List of content item IDs to classify
    
    Returns:
        Classification results
    """
    from app.workers.ai_processing import process_content_classification
    
    try:
        results = process_content_classification(content_ids)
        return {
            "status": "completed",
            "processed": len(content_ids),
            "results": results
        }
    except Exception as exc:
        logger.error("Content classification failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def calculate_rankings(
    self,
    config_id: Optional[str] = None,
    influencer_ids: Optional[List[str]] = None,
    full_recalculation: bool = False
) -> dict:
    """
    Calculate rankings for influencers.
    
    Args:
        config_id: Ranking config ID (None for default)
        influencer_ids: List of influencer IDs (None for all)
        full_recalculation: Whether to do full recalculation
    
    Returns:
        Calculation results
    """
    from app.workers.ranking import process_ranking_calculation
    
    try:
        result = process_ranking_calculation(
            config_id=config_id,
            influencer_ids=influencer_ids,
            full_recalculation=full_recalculation
        )
        return {
            "status": "completed",
            "processed": result.get("count", 0)
        }
    except Exception as exc:
        logger.error("Ranking calculation failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(bind=True, max_retries=2)
def sync_platform_account(self, account_id: str, platform: str) -> dict:
    """
    Sync a social account from a platform.
    
    Args:
        account_id: Social account ID
        platform: Platform name (youtube, github, etc.)
    
    Returns:
        Sync results
    """
    from app.workers.ingestion import process_account_sync
    
    try:
        result = process_account_sync(account_id, platform)
        return {
            "status": "completed",
            "account_id": account_id,
            "platform": platform,
            "new_content": result.get("new_content", 0)
        }
    except Exception as exc:
        logger.error(
            "Account sync failed",
            account_id=account_id,
            platform=platform,
            error=str(exc)
        )
        raise self.retry(exc=exc, countdown=300)


@celery_app.task
def send_notification(user_id: str, notification_type: str, data: dict) -> dict:
    """
    Send notification to user.
    
    Args:
        user_id: User ID
        notification_type: Type of notification
        data: Notification data
    
    Returns:
        Notification result
    """
    logger.info(
        "Sending notification",
        user_id=user_id,
        notification_type=notification_type
    )
    
    # TODO: Implement actual notification sending
    
    return {
        "status": "sent",
        "user_id": user_id,
        "type": notification_type
    }


@celery_app.task
def generate_weekly_digest(user_id: str) -> dict:
    """
    Generate weekly digest for user.
    
    Args:
        user_id: User ID
    
    Returns:
        Digest generation result
    """
    logger.info("Generating weekly digest", user_id=user_id)
    
    # TODO: Implement digest generation
    
    return {
        "status": "generated",
        "user_id": user_id
    }
