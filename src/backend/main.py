import asyncio
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from app.websocket.manager import ConnectionManager

app = FastAPI(
    title="ValueVerse API",
    description="API for the Value Realization Operating System",
    version="1.0.0",
)

# Add GZip compression middleware for responses larger than 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """On startup, create a background task to clean up stale connections."""
    asyncio.create_task(manager.cleanup_stale_connections())

@app.get("/health", tags=["Health"])
async def health_check():
    """Check the health of the application."""
    return {"status": "ok"}
