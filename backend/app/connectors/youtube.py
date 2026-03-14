"""
YouTube Data API connector.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from app.connectors.base import AuthenticationError, BaseConnector, ConnectorError, RateLimitError
from app.core.logging import get_logger

logger = get_logger(__name__)


class YouTubeConnector(BaseConnector):
    """Connector for YouTube Data API."""
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    # Quota costs
    QUOTA_COSTS = {
        "search.list": 100,
        "videos.list": 1,
        "channels.list": 1,
        "playlistItems.list": 1,
        "subscriptions.list": 1,
    }
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session."""
        if not self._session:
            self._session = aiohttp.ClientSession()
    
    async def close(self):
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def get_quota_limit(self) -> int:
        """YouTube API quota is 10,000 units per day."""
        return 10000
    
    async def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        method: str = "GET"
    ) -> Dict[str, Any]:
        """Make API request to YouTube."""
        
        self._check_rate_limit()
        
        if not self.api_key:
            raise AuthenticationError("YouTube API key not configured")
        
        if not self._session:
            await self.initialize()
        
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params["key"] = self.api_key
        
        # Track quota usage
        quota_cost = self.QUOTA_COSTS.get(endpoint, 1)
        self._track_api_call(quota_cost)
        
        try:
            async with self._session.request(
                method=method,
                url=url,
                params=params
            ) as response:
                if response.status == 403:
                    error_data = await response.json()
                    if "quotaExceeded" in str(error_data):
                        raise RateLimitError("YouTube API quota exceeded")
                    raise AuthenticationError("Invalid API key")
                
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                
                if response.status != 200:
                    text = await response.text()
                    raise ConnectorError(
                        f"YouTube API error: {response.status} - {text}",
                        status_code=response.status
                    )
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise ConnectorError(f"HTTP error: {str(e)}")
    
    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Get channel information."""
        
        # Handle channel ID formats
        if channel_id.startswith("@"):
            # Username format - need to search
            params = {"part": "snippet,statistics", "forHandle": channel_id}
        elif channel_id.startswith("UC"):
            # Standard channel ID
            params = {"part": "snippet,statistics", "id": channel_id}
        else:
            # Try as username
            params = {"part": "snippet,statistics", "forHandle": channel_id}
        
        data = await self._make_request("channels", params)
        
        items = data.get("items", [])
        if not items:
            raise ConnectorError(f"Channel not found: {channel_id}")
        
        channel = items[0]
        snippet = channel.get("snippet", {})
        stats = channel.get("statistics", {})
        
        return {
            "id": channel.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "published_at": snippet.get("publishedAt"),
            "country": snippet.get("country"),
            "subscriber_count": int(stats.get("subscriberCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
            "view_count": int(stats.get("viewCount", 0)),
            "thumbnail_url": self._get_thumbnail_url(snippet.get("thumbnails", {}))
        }
    
    async def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Get channel's recent videos."""
        
        # Get upload playlist ID
        channel_info = await self.get_channel_info(channel_id)
        
        # For now, use search to get recent videos
        # Note: This is expensive (100 quota per request)
        params = {
            "part": "snippet",
            "channelId": channel_info["id"],
            "order": "date",
            "type": "video",
            "maxResults": min(max_results, 50)
        }
        
        data = await self._make_request("search", params)
        
        videos = []
        video_ids = []
        
        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                video_ids.append(video_id)
                videos.append({
                    "id": video_id,
                    "title": item.get("snippet", {}).get("title"),
                    "description": item.get("snippet", {}).get("description"),
                    "published_at": item.get("snippet", {}).get("publishedAt"),
                    "thumbnail_url": self._get_thumbnail_url(
                        item.get("snippet", {}).get("thumbnails", {})
                    )
                })
        
        # Get video statistics
        if video_ids:
            stats_data = await self._get_video_stats(video_ids)
            
            for video in videos:
                stats = stats_data.get(video["id"], {})
                video.update(stats)
        
        return videos
    
    async def _get_video_stats(self, video_ids: List[str]) -> Dict[str, Dict]:
        """Get statistics for videos."""
        
        params = {
            "part": "statistics,contentDetails",
            "id": ",".join(video_ids[:50])  # Max 50 per request
        }
        
        data = await self._make_request("videos", params)
        
        stats = {}
        for item in data.get("items", []):
            video_id = item.get("id")
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})
            
            stats[video_id] = {
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(statistics.get("commentCount", 0)),
                "duration": content_details.get("duration")
            }
            
            # Parse duration
            duration_str = content_details.get("duration", "")
            if duration_str:
                stats[video_id]["duration_seconds"] = self._parse_duration(duration_str)
        
        return stats
    
    def _get_thumbnail_url(self, thumbnails: Dict) -> Optional[str]:
        """Get best available thumbnail URL."""
        for quality in ["maxres", "standard", "high", "medium", "default"]:
            if quality in thumbnails:
                return thumbnails[quality].get("url")
        return None
    
    def _parse_duration(self, duration: str) -> Optional[int]:
        """Parse ISO 8601 duration to seconds."""
        import re
        
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        if not match:
            return None
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
