from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.database import init_db
from app.api import upload, analysis, health, auth, drone

# 速率限制器
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="HKAIC - AI Drone Flight Intelligence SaaS API",
    description="Backend SaaS API for drone flight log analysis with AI-powered insights, multi-tenant support, subscription management, and real drone control capabilities",
    version="2.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置速率限制
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    
    # 启动健康检查任务
    from app.health_checker import start_health_checks
    from app.drone_manager import drone_manager
    await start_health_checks(drone_manager, interval=60)
    logger.info("Health checker started on startup")

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(auth.subscription_router)
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(drone.router)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "HKAIC - AI Drone Flight Intelligence SaaS",
        "version": "2.2.0",
        "status": "running",
        "features": [
            "Multi-tenant architecture",
            "User authentication & authorization",
            "Subscription management",
            "Flight log analysis",
            "AI-powered insights",
            "Quota management",
            "Real drone connection & control",
            "MAVSDK integration",
            "Rate limiting",
            "Audit logging"
        ],
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
