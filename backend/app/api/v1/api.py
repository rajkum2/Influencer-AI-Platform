"""
API router configuration.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    content,
    crm,
    influencers,
    rankings,
    search,
    technologies,
    users,
    watchlists,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(influencers.router, prefix="/influencers", tags=["Influencers"])
api_router.include_router(content.router, prefix="/content", tags=["Content"])
api_router.include_router(technologies.router, prefix="/technologies", tags=["Technologies"])
api_router.include_router(rankings.router, prefix="/rankings", tags=["Rankings"])
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["Watchlists"])
api_router.include_router(crm.router, prefix="/crm", tags=["CRM"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
