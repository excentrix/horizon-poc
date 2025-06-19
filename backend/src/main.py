# backend/src/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
from contextlib import asynccontextmanager
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from api.chat import router as chat_router

# Initialize Sentry
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.3,
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Horizon API...")
    yield
    # Shutdown
    print("⏹️ Shutting down Horizon API...")

app = FastAPI(
    title="Horizon API",
    description="AI-powered adaptive learning platform",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(chat_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.azurecontainerapps.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "horizon-api"}

@app.get("/")
async def root():
    return {"message": "Welcome to Horizon API", "version": "0.1.0"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENV") == "development" else False
    )