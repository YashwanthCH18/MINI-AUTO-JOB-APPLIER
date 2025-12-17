"""
Job Fetcher Stack - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.routes import router
from app.config import get_settings

# Create FastAPI app
app = FastAPI(
    title="Job Fetcher Stack",
    description="Fetches jobs from portals (LinkedIn, Naukri, Indeed) and stores them in Supabase",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Job Fetcher Stack",
        "version": "1.0.0",
        "docs": "/docs"
    }


# AWS Lambda handler
handler = Mangum(app, lifespan="off")
