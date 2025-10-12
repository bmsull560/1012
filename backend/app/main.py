from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import websocket

app = FastAPI(
    title="ValueVerse API",
    description="B2B Value Realization Operating System",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include WebSocket router
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])

@app.get("/")
def read_root():
    return {
        "message": "Welcome to ValueVerse API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/health")
def api_health():
    return {"status": "healthy", "api_version": "v1"}
