"""
Health Check Routes
Similar to a HealthController in NestJS
"""
from fastapi import APIRouter

# Create router (like @Controller() decorator in NestJS)
router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    Similar to @Get('health') in NestJS controller
    """
    return {
        "status": "healthy",
        "service": "RAG Backend"
    }

