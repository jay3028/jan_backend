"""
Routers initialization
"""
from .auth import router as auth_router
from .workers import router as workers_router
from .companies import router as companies_router
from .police import router as police_router
from .verification import router as verification_router
from .admin import router as admin_router

__all__ = [
    'auth_router',
    'workers_router',
    'companies_router',
    'police_router',
    'verification_router',
    'admin_router'
]

