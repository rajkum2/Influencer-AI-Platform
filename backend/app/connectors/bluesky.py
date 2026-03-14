"""
Bluesky API connector.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from app.connectors.base import AuthenticationError, BaseConnector, ConnectorError
from app.core.logging import get_logger

logger = get_logger(__name__)


class BlueskyConnector(BaseConnector):
    """Connector for Bluesky API."""
    
    BASE_URL = "https://api.bsky.app"
    
    def __init__(self, handle: Optional[str] = None, password: Optional[str] = None):
        super().__init__()
        self.handle = handle
        self.password = password
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_token: Optional[str] = None
    
    async def initialize(self):
        """Initialize HTTP session."""
        if not self._session:
            self._session = aiohttp.ClientSession()
            
            # Authenticate if credentials provided
            if self.handle and self.password:
                await self._authenticate()
    
    async def close(self):
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _authenticate(self):
        """Authenticate with Bluesky."""
        if not self._session:
            return
        
        try:
            async with self._session.post(
                "https://bsky.social/xrpc/com.atproto.server.createSession",
                json={
                    "identifier": self.handle,
                    "password": self.password
                }
            ) as response:
                if response.status != 200:
                    raise AuthenticationError("Failed to authenticate with Bluesky")
                
                data = await response.json()
                self._auth_token = data.get("accessJwt")
        except aiohttp.ClientError as e:
            raise ConnectorError(f"Authentication error: {str(e)}")
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Make API request to Bluesky."""
        
        if not self._session:
            await self.initialize()
        
        url = f"{self.BASE_URL}/xrpc/{endpoint}"
        headers = {}
        
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        
        try:
            async with self._session.get(url, params=params, headers=headers) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid authentication")
                
                if response.status != 200:
                    text = await response.text()
                    raise ConnectorError(
                        f"Bluesky API error: {response.status} - {text}",
                        status_code=response.status
                    )
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise ConnectorError(f"HTTP error: {str(e)}")
    
    async def get_user_info(self, handle: str) -> Dict[str, Any]:
        """Get user profile information."""
        
        data = await self._make_request(
            "app.bsky.actor.getProfile",
            {"actor": handle}
        )
        
        return {
            "did": data.get("did"),
            "handle": data.get("handle"),
            "display_name": data.get("displayName"),
            "description": data.get("description"),
            "avatar": data.get("avatar"),
            "banner": data.get("banner"),
            "followers_count": data.get("followersCount"),
            "following_count": data.get("followsCount"),
            "posts_count": data.get("postsCount"),
            "indexed_at": data.get("indexedAt"),
        }
    
    async def get_user_posts(
        self,
        handle: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's posts."""
        
        # First get the user's DID
        profile = await self.get_user_info(handle)
        did = profile["did"]
        
        posts = []
        cursor = None
        
        while len(posts) < max_results:
            params = {
                "actor": did,
                "limit": min(100, max_results - len(posts))
            }
            if cursor:
                params["cursor"] = cursor
            
            data = await self._make_request(
                "app.bsky.feed.getAuthorFeed",
                params
            )
            
            feed = data.get("feed", [])
            if not feed:
                break
            
            for item in feed:
                post = item.get("post", {})
                record = post.get("record", {})
                
                posts.append({
                    "uri": post.get("uri"),
                    "cid": post.get("cid"),
                    "text": record.get("text"),
                    "created_at": record.get("createdAt"),
                    "reply_count": post.get("replyCount"),
                    "repost_count": post.get("repostCount"),
                    "like_count": post.get("likeCount"),
                    "indexed_at": post.get("indexedAt"),
                })
            
            cursor = data.get("cursor")
            if not cursor:
                break
        
        return posts[:max_results]
    
    async def search_users(self, query: str, max_results: int = 25) -> List[Dict[str, Any]]:
        """Search for users."""
        
        data = await self._make_request(
            "app.bsky.actor.searchActors",
            {"q": query, "limit": min(100, max_results)}
        )
        
        users = []
        for actor in data.get("actors", []):
            users.append({
                "did": actor.get("did"),
                "handle": actor.get("handle"),
                "display_name": actor.get("displayName"),
                "description": actor.get("description"),
                "avatar": actor.get("avatar"),
                "followers_count": actor.get("followersCount"),
                "indexed_at": actor.get("indexedAt"),
            })
        
        return users
