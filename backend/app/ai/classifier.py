"""
AI content classifier using OpenAI.
"""

import json
from typing import Dict, List, Optional

import openai

from app.core.logging import get_logger

logger = get_logger(__name__)


class ContentClassifier:
    """Classify content using AI."""
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.client = openai.AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None
        self.model = model
    
    async def classify_content(
        self,
        text: str,
        technologies: List[Dict[str, str]]
    ) -> Dict:
        """
        Classify content and extract relevant technologies.
        
        Args:
            text: Content text to classify
            technologies: List of available technologies
        
        Returns:
            Classification results
        """
        
        if not self.client:
            logger.warning("OpenAI client not configured, returning empty classification")
            return {
                "summary": None,
                "technologies": [],
                "quality_score": 0.5,
                "spam_score": 0.0
            }
        
        # Truncate text if too long
        max_length = 8000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        # Build technology list
        tech_list = "\n".join([f"- {t['id']}: {t['name']}" for t in technologies])
        
        prompt = f"""Analyze the following content and provide:
1. A brief summary (2-3 sentences)
2. Relevant technologies/topics from the list below
3. Quality score (0.0 to 1.0) based on depth, originality, and educational value
4. Spam score (0.0 to 1.0) - higher means more likely spam/promotional

Available technologies:
{tech_list}

Content:
{text}

Respond in JSON format:
{{
    "summary": "brief summary",
    "technologies": [
        {{"technology_id": "id", "relevance_score": 0.8, "confidence": 0.9}}
    ],
    "quality_score": 0.7,
    "spam_score": 0.1
}}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI content classifier. Analyze content and provide structured classifications."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate and clean result
            return {
                "summary": result.get("summary"),
                "technologies": result.get("technologies", []),
                "quality_score": max(0, min(1, result.get("quality_score", 0.5))),
                "spam_score": max(0, min(1, result.get("spam_score", 0)))
            }
        
        except Exception as e:
            logger.error("Classification failed", error=str(e))
            return {
                "summary": None,
                "technologies": [],
                "quality_score": 0.5,
                "spam_score": 0
            }
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate text embedding."""
        
        if not self.client:
            return None
        
        try:
            # Truncate text
            text = text[:8000]
            
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            return None
    
    async def summarize_content(self, text: str, max_length: int = 200) -> Optional[str]:
        """Generate a summary of content."""
        
        if not self.client:
            return None
        
        # Truncate input
        text = text[:8000]
        
        prompt = f"Summarize the following content in {max_length} characters or less:\n\n{text}"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a content summarizer. Create concise, informative summaries."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            summary = response.choices[0].message.content.strip()
            return summary[:max_length]
        
        except Exception as e:
            logger.error("Summarization failed", error=str(e))
            return None
