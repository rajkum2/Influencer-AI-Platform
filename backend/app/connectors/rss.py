"""
RSS/Blog connector for scraping articles and newsletters.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector, ConnectorError
from app.core.logging import get_logger

logger = get_logger(__name__)


class RSSConnector(BaseConnector):
    """Connector for RSS feeds and blogs."""
    
    def __init__(self):
        super().__init__()
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session."""
        if not self._session:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; InfluencerPlatform/1.0)"
                }
            )
    
    async def close(self):
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _fetch_url(self, url: str) -> str:
        """Fetch content from URL."""
        
        if not self._session:
            await self.initialize()
        
        try:
            async with self._session.get(url, timeout=30) as response:
                if response.status != 200:
                    raise ConnectorError(
                        f"HTTP {response.status}",
                        status_code=response.status
                    )
                
                return await response.text()
        
        except aiohttp.ClientError as e:
            raise ConnectorError(f"Fetch error: {str(e)}")
    
    def _find_rss_feed(self, html: str, base_url: str) -> Optional[str]:
        """Find RSS feed URL from HTML."""
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Look for RSS link tags
        feed_types = [
            "application/rss+xml",
            "application/atom+xml",
            "application/feed+json",
            "application/json",
        ]
        
        for feed_type in feed_types:
            link = soup.find("link", {"type": feed_type})
            if link and link.get("href"):
                return urljoin(base_url, link["href"])
        
        # Common feed paths
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        common_paths = [
            "/feed",
            "/feed.xml",
            "/rss",
            "/rss.xml",
            "/atom.xml",
            "/index.xml",
            "/blog/feed",
            "/feed/",
        ]
        
        for path in common_paths:
            return urljoin(base, path)
        
        return None
    
    async def get_feed_info(self, url: str) -> Dict[str, Any]:
        """Get RSS feed information."""
        
        # Fetch the URL
        content = await self._fetch_url(url)
        
        # Try to parse as RSS
        feed = feedparser.parse(content)
        
        if feed.bozo and not feed.entries:
            # Might be HTML, try to find RSS link
            rss_url = self._find_rss_feed(content, url)
            if rss_url and rss_url != url:
                return await self.get_feed_info(rss_url)
            
            raise ConnectorError("No valid RSS feed found")
        
        return {
            "title": feed.feed.get("title"),
            "description": feed.feed.get("description"),
            "link": feed.feed.get("link"),
            "url": url,
            "language": feed.feed.get("language"),
            "updated": feed.feed.get("updated"),
            "entry_count": len(feed.entries),
        }
    
    async def get_entries(
        self,
        url: str,
        max_results: int = 50,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get RSS feed entries."""
        
        content = await self._fetch_url(url)
        feed = feedparser.parse(content)
        
        entries = []
        for entry in feed.entries[:max_results]:
            # Parse published date
            published = None
            if entry.get("published_parsed"):
                published = datetime(*entry.published_parsed[:6])
            elif entry.get("updated_parsed"):
                published = datetime(*entry.updated_parsed[:6])
            
            # Skip if before since date
            if since and published and published < since:
                continue
            
            # Extract content
            content_html = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else entry.get("summary", "")
            
            # Clean content
            soup = BeautifulSoup(content_html, "html.parser")
            content_text = soup.get_text(separator=" ", strip=True)
            
            entries.append({
                "id": entry.get("id") or entry.get("link"),
                "title": entry.get("title"),
                "link": entry.get("link"),
                "published_at": published,
                "author": entry.get("author"),
                "summary": entry.get("summary", "")[:500],
                "content": content_text[:5000],
                "tags": [tag.term for tag in entry.get("tags", [])],
            })
        
        return entries
    
    async def get_substack_posts(
        self,
        subdomain: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Get posts from Substack newsletter."""
        
        url = f"https://{subdomain}.substack.com/feed"
        return await self.get_entries(url, max_results)
    
    async def get_medium_posts(
        self,
        username: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Get posts from Medium."""
        
        url = f"https://medium.com/feed/@{username}"
        return await self.get_entries(url, max_results)
    
    async def get_dev_to_posts(
        self,
        username: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Get posts from Dev.to."""
        
        url = f"https://dev.to/feed/{username}"
        return await self.get_entries(url, max_results)
