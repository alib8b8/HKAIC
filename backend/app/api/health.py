from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "HKAIC API",
        "environment": settings.environment
    }


@router.get("/services")
async def services_status():
    """Check status of integrated services"""
    services = {
        "database": "available",
        "openai": "configured" if settings.openai_api_key else "not configured",
        "supabase": "configured" if settings.supabase_url and settings.supabase_key else "not configured"
    }
    return services
