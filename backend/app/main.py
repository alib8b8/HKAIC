from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api import upload, analysis, health, auth, drone

# Create FastAPI app
app = FastAPI(
    title="HKAIC - AI Drone Flight Intelligence SaaS API",
    description="Backend SaaS API for drone flight log analysis with AI-powered insights, multi-tenant support, subscription management, and real drone control capabilities",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
        "version": "2.1.0",
        "status": "running",
        "features": [
            "Multi-tenant architecture",
            "User authentication & authorization",
            "Subscription management",
            "Flight log analysis",
            "AI-powered insights",
            "Quota management",
            "Real drone connection & control",
            "MAVSDK integration"
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
