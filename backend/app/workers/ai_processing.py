"""
AI processing workers for content classification and enrichment.
"""

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.classifier import ContentClassifier
from app.core.config import settings
from app.core.logging import get_logger
from app.db.base import SessionLocal
from app.models.content import ContentItem
from app.models.technology import ContentTechnology, Technology
from app.workers.celery_app import celery_app

logger = get_logger(__name__)

# Initialize classifier
classifier = ContentClassifier(
    openai_api_key=settings.openai_api_key,
    model=settings.openai_model
)


@celery_app.task(bind=True, max_retries=3)
def process_pending_content(self, batch_size: int = 50) -> dict:
    """
    Process pending content items with AI.
    
    Args:
        batch_size: Number of items to process
    
    Returns:
        Processing results
    """
    import asyncio
    return asyncio.run(_process_pending_content(batch_size))


async def _process_pending_content(batch_size: int) -> dict:
    """Async implementation of content processing."""
    
    async with SessionLocal() as db:
        # Get pending content
        result = await db.execute(
            select(ContentItem).where(
                ContentItem.processing_status == "pending"
            ).limit(batch_size)
        )
        content_items = result.scalars().all()
        
        processed = 0
        failed = 0
        
        for content in content_items:
            try:
                await _process_single_content(db, content)
                processed += 1
            except Exception as e:
                logger.error(
                    "Content processing failed",
                    content_id=str(content.id),
                    error=str(e)
                )
                content.processing_status = "failed"
                await db.commit()
                failed += 1
        
        return {
            "total": len(content_items),
            "processed": processed,
            "failed": failed
        }


async def _process_single_content(db: AsyncSession, content: ContentItem) -> None:
    """Process a single content item."""
    
    # Update status
    content.processing_status = "processing"
    await db.commit()
    
    # Prepare text for classification
    text = f"{content.title or ''}\n\n{content.body_text or ''}"
    
    if not text.strip():
        content.processing_status = "completed"
        await db.commit()
        return
    
    # Get technologies
    tech_result = await db.execute(select(Technology))
    technologies = tech_result.scalars().all()
    
    # Classify content
    classification = await classifier.classify_content(
        text=text,
        technologies=[{"id": str(t.id), "name": t.name} for t in technologies]
    )
    
    # Update content
    content.summary = classification.get("summary")
    content.quality_score = classification.get("quality_score")
    content.spam_score = classification.get("spam_score")
    
    # Add technology mappings
    for tech_mapping in classification.get("technologies", []):
        content_tech = ContentTechnology(
            content_id=content.id,
            technology_id=UUID(tech_mapping["technology_id"]),
            relevance_score=tech_mapping.get("relevance_score"),
            confidence=tech_mapping.get("confidence"),
            detection_method="ai_classified"
        )
        db.add(content_tech)
    
    content.processing_status = "completed"
    content.is_indexed = True
    
    await db.commit()
    
    logger.info(
        "Content processed",
        content_id=str(content.id),
        technologies=len(classification.get("technologies", []))
    )


def process_content_classification(content_ids: List[str]) -> List[dict]:
    """Process content classification for specific IDs."""
    import asyncio
    return asyncio.run(_process_content_classification(content_ids))


async def _process_content_classification(content_ids: List[str]) -> List[dict]:
    """Async implementation of content classification."""
    
    results = []
    
    async with SessionLocal() as db:
        for content_id in content_ids:
            content = await db.get(ContentItem, UUID(content_id))
            
            if not content:
                results.append({
                    "content_id": content_id,
                    "status": "not_found"
                })
                continue
            
            try:
                await _process_single_content(db, content)
                results.append({
                    "content_id": content_id,
                    "status": "completed"
                })
            except Exception as e:
                results.append({
                    "content_id": content_id,
                    "status": "failed",
                    "error": str(e)
                })
    
    return results
