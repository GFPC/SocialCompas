from fastapi import APIRouter
from .places import router as places_router
from .profile import router as profile_router
from .favorites import router as favorites_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(places_router)
v1_router.include_router(profile_router)
v1_router.include_router(favorites_router)

__all__ = ["v1_router"]
