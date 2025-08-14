from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from contextlib import asynccontextmanager

from app.routers import v1

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup events
    yield
    # Shutdown events

def create_app():
    app = FastAPI(
        title="HTIDP - HyperText ID Protocol",
        description="RESTful API protocol for sharing contact information and keeping it up to date",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware with more restrictive settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["GET", "POST", "HEAD"],
        allow_headers=["*"],
        expose_headers=["Last-Modified"],
    )
    
    # Mount templates directory for static files if needed
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    if os.path.exists(templates_dir):
        app.mount("/templates", StaticFiles(directory=templates_dir), name="templates")
    
    # Include routers without version prefix
    app.include_router(v1.router)
    
    return app

app = create_app()