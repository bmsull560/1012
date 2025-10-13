"""
ValueVerse Platform - Main FastAPI Application
Living Value Graph Backend with Agent Orchestration
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
from pydantic import BaseModel, Field
import asyncpg
import redis.asyncio as redis
from passlib.context import CryptContext
import jwt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================
# Configuration
# =====================================================

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/valueverse")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
settings = Settings()

# =====================================================
# Database Connection Pool
# =====================================================

class Database:
    pool: asyncpg.Pool = None
    
    @classmethod
    async def connect(cls):
        cls.pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=10,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database connection pool created")
    
    @classmethod
    async def disconnect(cls):
        if cls.pool:
            await cls.pool.close()
            logger.info("Database connection pool closed")
    
    @classmethod
    async def execute(cls, query: str, *args):
        async with cls.pool.acquire() as connection:
            return await connection.execute(query, *args)
    
    @classmethod
    async def fetch(cls, query: str, *args):
        async with cls.pool.acquire() as connection:
            return await connection.fetch(query, *args)
    
    @classmethod
    async def fetchrow(cls, query: str, *args):
        async with cls.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

# =====================================================
# Redis Connection
# =====================================================

class Cache:
    client: redis.Redis = None
    
    @classmethod
    async def connect(cls):
        cls.client = await redis.from_url(settings.REDIS_URL)
        logger.info("Redis connection established")
    
    @classmethod
    async def disconnect(cls):
        if cls.client:
            await cls.client.close()
            logger.info("Redis connection closed")

# =====================================================
# Lifespan Management
# =====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await Database.connect()
    await Cache.connect()
    logger.info("ValueVerse Platform started")
    
    yield
    
    # Shutdown
    await Database.disconnect()
    await Cache.disconnect()
    logger.info("ValueVerse Platform stopped")

# =====================================================
# FastAPI Application
# =====================================================

app = FastAPI(
    title="ValueVerse Platform API",
    description="Living Value Graph with Agent Orchestration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# Authentication
# =====================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    tenant_id: Optional[str] = None

class User(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    tenant_id: str
    role_id: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, tenant_id=tenant_id)
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await Database.fetchrow(
        "SELECT * FROM users WHERE email = $1 AND tenant_id = $2",
        token_data.email, uuid.UUID(token_data.tenant_id)
    )
    if user is None:
        raise credentials_exception
    return User(**dict(user))

# =====================================================
# Authentication Endpoints
# =====================================================

@app.post("/api/v1/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await Database.fetchrow(
        "SELECT * FROM users WHERE email = $1",
        form_data.username
    )
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "tenant_id": str(user["tenant_id"])},
        expires_delta=access_token_expires
    )
    
    # Update last login
    await Database.execute(
        "UPDATE users SET last_login_at = $1 WHERE id = $2",
        datetime.utcnow(), user["id"]
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# =====================================================
# Value Model Endpoints
# =====================================================

class ValueModelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    company_id: Optional[str] = None
    target_value: Optional[float] = None
    hypothesis: Dict[str, Any] = Field(default_factory=dict)

class ValueModel(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    stage: str
    status: str
    target_value: Optional[float]
    realized_value: float
    confidence_score: float
    created_at: datetime
    updated_at: datetime

@app.post("/api/v1/value-models", response_model=ValueModel)
async def create_value_model(
    model: ValueModelCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new value model"""
    model_id = uuid.uuid4()
    
    result = await Database.fetchrow(
        """
        INSERT INTO value_models (
            id, tenant_id, name, description, company_id,
            target_value, hypothesis, created_by, updated_by
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
        """,
        model_id,
        uuid.UUID(current_user.tenant_id),
        model.name,
        model.description,
        uuid.UUID(model.company_id) if model.company_id else None,
        model.target_value,
        json.dumps(model.hypothesis),
        uuid.UUID(current_user.id),
        uuid.UUID(current_user.id)
    )
    
    return ValueModel(**dict(result))

@app.get("/api/v1/value-models", response_model=List[ValueModel])
async def list_value_models(
    current_user: User = Depends(get_current_user),
    stage: Optional[str] = None,
    status: Optional[str] = None
):
    """List value models for the current tenant"""
    query = "SELECT * FROM value_models WHERE tenant_id = $1"
    params = [uuid.UUID(current_user.tenant_id)]
    
    if stage:
        query += f" AND stage = ${len(params) + 1}"
        params.append(stage)
    
    if status:
        query += f" AND status = ${len(params) + 1}"
        params.append(status)
    
    query += " ORDER BY created_at DESC"
    
    results = await Database.fetch(query, *params)
    return [ValueModel(**dict(row)) for row in results]

@app.get("/api/v1/value-models/{model_id}", response_model=ValueModel)
async def get_value_model(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific value model"""
    result = await Database.fetchrow(
        "SELECT * FROM value_models WHERE id = $1 AND tenant_id = $2",
        uuid.UUID(model_id),
        uuid.UUID(current_user.tenant_id)
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Value model not found")
    
    return ValueModel(**dict(result))

# =====================================================
# Agent WebSocket Connection
# =====================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def broadcast(self, message: str, tenant_id: str):
        for client_id, connection in self.active_connections.items():
            if client_id.startswith(tenant_id):
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process different message types
            if message["type"] == "agent:message":
                # Process agent message
                response = await process_agent_message(message)
                await manager.send_personal_message(
                    json.dumps(response),
                    client_id
                )
            
            elif message["type"] == "agent:handoff:request":
                # Handle agent handoff
                response = await handle_agent_handoff(message)
                await manager.send_personal_message(
                    json.dumps(response),
                    client_id
                )
            
            elif message["type"] == "value:update":
                # Broadcast value updates to tenant
                tenant_id = client_id.split("-")[0]
                await manager.broadcast(
                    json.dumps(message),
                    tenant_id
                )
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# =====================================================
# Agent Processing Functions
# =====================================================

async def process_agent_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Process a message sent to an agent"""
    agent_name = message.get("agent")
    user_message = message.get("message")
    context = message.get("context", {})
    
    # TODO: Integrate with actual AI service
    # For now, return a mock response
    
    response = {
        "type": "agent:response",
        "agent": agent_name,
        "content": f"I understand you want to discuss: {user_message}",
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "confidence": 0.95,
            "reasoning": ["Analyzed user intent", "Generated response"],
            "processingTime": 1.2
        }
    }
    
    # Simulate thinking state
    await asyncio.sleep(0.5)
    
    return response

async def handle_agent_handoff(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle handoff between agents"""
    from_agent = message.get("fromAgent")
    to_agent = message.get("toAgent")
    context = message.get("context", {})
    
    response = {
        "type": "agent:handoff",
        "fromAgent": from_agent,
        "toAgent": to_agent,
        "context": context,
        "reason": "Specialized expertise required",
        "requiresApproval": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return response

# =====================================================
# Health Check
# =====================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        await Database.execute("SELECT 1")
        
        # Check Redis connection
        await Cache.client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "connected",
                "cache": "connected",
                "websocket": "active"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# =====================================================
# Root Endpoint
# =====================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "ValueVerse Platform API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
