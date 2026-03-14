"""
GitHub API connector.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from app.connectors.base import AuthenticationError, BaseConnector, ConnectorError, RateLimitError
from app.core.logging import get_logger

logger = get_logger(__name__)


class GitHubConnector(BaseConnector):
    """Connector for GitHub API."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        super().__init__(token)
        self._session: Optional[aiohttp.ClientSession] = None
        self._headers = {}
    
    async def initialize(self):
        """Initialize HTTP session."""
        if not self._session:
            self._headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "InfluencerPlatform/1.0"
            }
            if self.api_key:
                self._headers["Authorization"] = f"token {self.api_key}"
            
            self._session = aiohttp.ClientSession(headers=self._headers)
    
    async def close(self):
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any] = None
    ) -> Any:
        """Make API request to GitHub."""
        
        if not self._session:
            await self.initialize()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            async with self._session.get(url, params=params) as response:
                # Check rate limit
                remaining = response.headers.get("X-RateLimit-Remaining")
                if remaining and int(remaining) == 0:
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    raise RateLimitError(
                        "GitHub API rate limit exceeded",
                        retry_after=reset_time - int(datetime.utcnow().timestamp())
                    )
                
                if response.status == 401:
                    raise AuthenticationError("Invalid GitHub token")
                
                if response.status == 403:
                    raise RateLimitError("GitHub API rate limit exceeded")
                
                if response.status == 404:
                    raise ConnectorError("Resource not found", status_code=404)
                
                if response.status != 200:
                    text = await response.text()
                    raise ConnectorError(
                        f"GitHub API error: {response.status} - {text}",
                        status_code=response.status
                    )
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise ConnectorError(f"HTTP error: {str(e)}")
    
    async def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get user information."""
        
        data = await self._make_request(f"users/{username}")
        
        return {
            "id": data.get("id"),
            "login": data.get("login"),
            "name": data.get("name"),
            "bio": data.get("bio"),
            "company": data.get("company"),
            "location": data.get("location"),
            "blog": data.get("blog"),
            "email": data.get("email"),
            "twitter_username": data.get("twitter_username"),
            "followers": data.get("followers"),
            "following": data.get("following"),
            "public_repos": data.get("public_repos"),
            "public_gists": data.get("public_gists"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "avatar_url": data.get("avatar_url"),
            "html_url": data.get("html_url")
        }
    
    async def get_user_repos(
        self,
        username: str,
        max_results: int = 30
    ) -> List[Dict[str, Any]]:
        """Get user's repositories."""
        
        params = {
            "sort": "updated",
            "direction": "desc",
            "per_page": min(max_results, 100)
        }
        
        data = await self._make_request(f"users/{username}/repos", params)
        
        repos = []
        for repo in data:
            repos.append({
                "id": repo.get("id"),
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "html_url": repo.get("html_url"),
                "description": repo.get("description"),
                "language": repo.get("language"),
                "created_at": repo.get("created_at"),
                "updated_at": repo.get("updated_at"),
                "pushed_at": repo.get("pushed_at"),
                "stargazers_count": repo.get("stargazers_count"),
                "watchers_count": repo.get("watchers_count"),
                "forks_count": repo.get("forks_count"),
                "open_issues_count": repo.get("open_issues_count"),
                "topics": repo.get("topics", []),
                "fork": repo.get("fork", False),
                "archived": repo.get("archived", False)
            })
        
        return repos
    
    async def get_repo_readme(self, owner: str, repo: str) -> Optional[str]:
        """Get repository README content."""
        
        try:
            data = await self._make_request(f"repos/{owner}/{repo}/readme")
            
            # README is base64 encoded
            import base64
            content = data.get("content", "")
            if content:
                return base64.b64decode(content).decode("utf-8")
            
            return None
        
        except ConnectorError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def get_user_activity(self, username: str) -> List[Dict[str, Any]]:
        """Get user's recent activity."""
        
        # Get events
        data = await self._make_request(
            f"users/{username}/events",
            {"per_page": 30}
        )
        
        activities = []
        for event in data:
            activities.append({
                "id": event.get("id"),
                "type": event.get("type"),
                "created_at": event.get("created_at"),
                "repo": event.get("repo", {}).get("name"),
                "payload": event.get("payload")
            })
        
        return activities
    
    async def get_repo_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get repository language breakdown."""
        
        data = await self._make_request(f"repos/{owner}/{repo}/languages")
        return data
