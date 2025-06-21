"""
Main API v1 router
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, ai, voice, memory, tasks

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"]) 