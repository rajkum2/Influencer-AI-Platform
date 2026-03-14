"""
Base schema classes and common types.
"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampMixin(BaseSchema):
    """Mixin for timestamp fields."""
    
    created_at: datetime
    updated_at: datetime


class IDMixin(BaseSchema):
    """Mixin for ID field."""
    
    id: str = Field(..., description="Unique identifier (UUID)")


T = TypeVar("T")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper."""
    
    items: List[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class ListParams(BaseSchema):
    """Base parameters for list endpoints."""
    
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")
    search: Optional[str] = Field(None, description="Search query")


class MessageResponse(BaseSchema):
    """Simple message response."""
    
    message: str


class ErrorResponse(BaseSchema):
    """Error response."""
    
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class BulkOperationRequest(BaseSchema):
    """Request for bulk operations."""
    
    ids: List[str] = Field(..., min_length=1, max_length=1000)


class BulkOperationResponse(BaseSchema):
    """Response for bulk operations."""
    
    success: int
    failed: int
    errors: List[dict] = []
