# backend/src/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from contextlib import asynccontextmanager
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from models.core import create_db_and_tables
from api.chat import router as chat_router
from api.chat_v2 import router as chat_v2_router

# Initialize Sentry only if DSN is properly configured
def init_sentry():
    sentry_dsn = os.getenv("SENTRY_DSN")
    
    # Only initialize if DSN is set and not empty
    if sentry_dsn and sentry_dsn.strip() and sentry_dsn.startswith(('https://', 'http://')):
        try:
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    FastApiIntegration(auto_enabling_integrations=False),
                    SqlalchemyIntegration(),
                ],
                traces_sample_rate=0.1,  # Reduced for development
                profiles_sample_rate=0.1,
                environment=os.getenv("ENV", "development"),
                release=f"horizon@{os.getenv('VERSION', '0.2.0')}",
                # Debug mode for development
                debug=os.getenv("ENV") == "development",
            )
            print("✅ Sentry initialized successfully")
            return True
        except Exception as e:
            print(f"⚠️  Sentry initialization failed: {e}")
            return False
    else:
        print("ℹ️  Sentry DSN not configured, skipping Sentry initialization")
        return False

# Initialize Sentry
sentry_enabled = init_sentry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Horizon API...")
    print(f"🌍 Environment: {os.getenv('ENV', 'development')}")
    print(f"📊 Sentry: {'Enabled' if sentry_enabled else 'Disabled'}")
    
    try:
        print("🗄️ Creating database tables...")
        create_db_and_tables()
        print("✅ Database ready!")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        if sentry_enabled:
            sentry_sdk.capture_exception(e)
        raise
    
    yield
    
    # Shutdown
    print("⏹️ Shutting down Horizon API...")
    if sentry_enabled:
        sentry_sdk.flush(timeout=5)

app = FastAPI(
    title="Horizon API",
    description="AI-powered adaptive learning platform with real-time chat",
    version="0.1.3",
    lifespan=lifespan,
    # Add more metadata
    contact={
        "name": "Horizon Support",
        "email": "support@horizon.ai",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
        "https://*.azurecontainerapps.io",
        "https://*.azurewebsites.net",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(chat_v2_router)  

@app.get("/health")
async def health_check():
    """Health check endpoint with system status."""
    return {
        "status": "healthy",
        "service": "horizon-api",
        "version": "0.1.2",
        "environment": os.getenv("ENV", "development"),
        "features": {
            "ai_enabled": bool(os.getenv("AZURE_OPENAI_ENDPOINT")),
            "database_connected": bool(os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")),
            "sentry_enabled": sentry_enabled,
            "agentic": True,
            "enhanced_memory": True,
            "background_processing": False
        },
         "apis": {
            "v1": "/api/chat/*",
            "v2": "/api/v2/chat/*"
        },
        "timestamp": "2025-01-24T12:00:00Z"  # Will be replaced with actual timestamp
    }

@app.get("/")
async def root():
    """API root with information."""
    return {
        "message": "Welcome to Horizon API v0.1.2",
        "description": "AI-powered adaptive learning platform",
        "features": [
            "Real-time AI chat with streaming",
            "Intelligent fact extraction",
            "Automated task creation",
            "Personalized learning paths"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "chat": "/api/chat/stream"
        },
         "apis": {
            "v1": "/api/chat/*",
            "v2": "/api/v2/chat/*"
        },
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for better error reporting."""
    if sentry_enabled:
        sentry_sdk.capture_exception(exc)
    
    print(f"Global exception: {exc}")
    
    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred. Our team has been notified.",
        "request_id": getattr(request.state, 'request_id', 'unknown')
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENV") == "development" else False,
        log_level="info",
        access_log=True,
        reload_dirs=["src"] if os.getenv("ENV") == "development" else None,
    )