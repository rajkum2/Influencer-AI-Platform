"""
Base connector class for platform integrations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectorError(Exception):
    """Base exception for connector errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class RateLimitError(ConnectorError):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class AuthenticationError(ConnectorError):
    """Authentication error."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class BaseConnector(ABC):
    """Base class for platform connectors."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._session = None
        self._quota_used = 0
        self._quota_reset_at = None
    
    @abstractmethod
    async def initialize(self):
        """Initialize the connector."""
        pass
    
    @abstractmethod
    async def close(self):
        """Close the connector."""
        pass
    
    @abstractmethod
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information."""
        pass
    
    @abstractmethod
    async def get_user_content(
        self,
        user_id: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's content."""
        pass
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _check_rate_limit(self):
        """Check if rate limit is exceeded."""
        if self._quota_reset_at and datetime.utcnow() < self._quota_reset_at:
            if self._quota_used >= self.get_quota_limit():
                raise RateLimitError(
                    "Quota exceeded",
                    retry_after=int((self._quota_reset_at - datetime.utcnow()).total_seconds())
                )
    
    def get_quota_limit(self) -> int:
        """Get the quota limit for this connector."""
        return 10000  # Default
    
    def get_quota_used(self) -> int:
        """Get the quota used."""
        return self._quota_used
    
    def _track_api_call(self, cost: int = 1):
        """Track an API call."""
        self._quota_used += cost
