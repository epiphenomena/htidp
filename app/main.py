from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(v1.router, prefix="/v1", tags=["v1"])
    
    return app

app = create_app()