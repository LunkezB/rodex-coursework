from fastapi import APIRouter

from app.api.routes import auth, health, persons, relationships, reports, sources

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(persons.router, prefix="/persons", tags=["persons"])
api_router.include_router(relationships.router, prefix="/relationships", tags=["relationships"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
