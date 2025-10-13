from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI()
SERVICE_NAME = os.path.basename(os.getcwd())
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))

@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def ready():
    return {"status": "ready"}

@app.get("/api/v1/metrics")
async def metrics():
    return {"service": SERVICE_NAME, "uptime": "99.9%"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
