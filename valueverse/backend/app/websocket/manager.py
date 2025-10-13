"""WebSocket connection manager for real-time synchronization"""

import json
from typing import Dict, List, Set, Any, Optional
from datetime import datetime
import asyncio
import socketio
from fastapi import FastAPI
import logging

from app.core.config import settings
from app.agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.BACKEND_CORS_ORIGINS,
    ping_interval=settings.WEBSOCKET_PING_INTERVAL,
    ping_timeout=settings.WEBSOCKET_PING_TIMEOUT,
)

# Create Socket.IO ASGI app
sio_app = socketio.ASGIApp(sio)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[str]] = {}  # room_id -> set of session_ids
        self.user_sessions: Dict[str, str] = {}  # session_id -> user_id
        self.session_data: Dict[str, Dict[str, Any]] = {}  # session_id -> session data
        self.orchestrator = AgentOrchestrator()
    
    async def connect(self, sid: str, user_id: str, room_id: str = "default"):
        """Handle new connection"""
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        
        self.active_connections[room_id].add(sid)
        self.user_sessions[sid] = user_id
        self.session_data[sid] = {
            "user_id": user_id,
            "room_id": room_id,
            "connected_at": datetime.utcnow().isoformat(),
            "canvas_state": {},
            "context": {}
        }
        
        await sio.enter_room(sid, room_id)
        logger.info(f"User {user_id} connected with session {sid} to room {room_id}")
        
        # Send initial state
        await self.send_initial_state(sid)
    
    async def disconnect(self, sid: str):
        """Handle disconnection"""
        if sid in self.session_data:
            room_id = self.session_data[sid].get("room_id", "default")
            if room_id in self.active_connections:
                self.active_connections[room_id].discard(sid)
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]
            
            user_id = self.user_sessions.get(sid)
            del self.user_sessions[sid]
            del self.session_data[sid]
            
            await sio.leave_room(sid, room_id)
            logger.info(f"User {user_id} disconnected (session {sid})")
    
    async def send_initial_state(self, sid: str):
        """Send initial state to newly connected client"""
        await sio.emit(
            "initial_state",
            {
                "connected": True,
                "timestamp": datetime.utcnow().isoformat(),
                "capabilities": [
                    "value_modeling",
                    "agent_orchestration",
                    "real_time_sync",
                    "pattern_matching"
                ]
            },
            room=sid
        )
    
    async def broadcast_to_room(self, room_id: str, event: str, data: Any, exclude_sid: Optional[str] = None):
        """Broadcast message to all connections in a room"""
        if room_id in self.active_connections:
            for sid in self.active_connections[room_id]:
                if sid != exclude_sid:
                    await sio.emit(event, data, room=sid)
    
    async def handle_user_input(self, sid: str, data: Dict[str, Any]):
        """Process user input and trigger agent response"""
        user_id = self.user_sessions.get(sid)
        session = self.session_data.get(sid, {})
        
        # Notify that agent is thinking
        await sio.emit("agent_thinking", {"status": "processing"}, room=sid)
        
        try:
            # Process through agent orchestrator
            result = await self.orchestrator.process_input(
                user_input=data.get("content", ""),
                context={
                    "user_id": user_id,
                    "session_id": sid,
                    "canvas_state": session.get("canvas_state", {}),
                    "template": data.get("context", {}).get("template"),
                    **data.get("context", {})
                }
            )
            
            # Send agent response
            await sio.emit(
                "agent_response",
                {
                    "content": result.get("response", ""),
                    "agent": result.get("agent", "ValueArchitect"),
                    "confidence": result.get("confidence", 0.8),
                    "reasoning": result.get("reasoning", []),
                    "timestamp": datetime.utcnow().isoformat()
                },
                room=sid
            )
            
            # Update canvas if needed
            if "canvas_update" in result:
                await self.update_canvas(sid, result["canvas_update"])
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            await sio.emit(
                "error",
                {"message": "Failed to process request", "error": str(e)},
                room=sid
            )
    
    async def update_canvas(self, sid: str, canvas_data: Dict[str, Any]):
        """Update canvas state and broadcast to room"""
        if sid in self.session_data:
            # Update session canvas state
            self.session_data[sid]["canvas_state"] = canvas_data
            
            # Get room ID
            room_id = self.session_data[sid].get("room_id", "default")
            
            # Broadcast canvas update to all in room
            await self.broadcast_to_room(
                room_id,
                "canvas_update",
                {
                    "components": canvas_data.get("components", []),
                    "template": canvas_data.get("template"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "updated_by": self.user_sessions.get(sid)
                },
                exclude_sid=None  # Include sender in update
            )
    
    async def handle_canvas_interaction(self, sid: str, data: Dict[str, Any]):
        """Handle direct canvas manipulation"""
        action = data.get("action")
        
        if action == "update_component":
            component_id = data.get("component_id")
            updates = data.get("updates", {})
            
            # Update component in canvas state
            if sid in self.session_data:
                canvas_state = self.session_data[sid].get("canvas_state", {})
                components = canvas_state.get("components", [])
                
                for component in components:
                    if component.get("id") == component_id:
                        component.update(updates)
                        break
                
                # Broadcast update
                await self.update_canvas(sid, canvas_state)
        
        elif action == "add_component":
            new_component = data.get("component")
            
            if sid in self.session_data and new_component:
                canvas_state = self.session_data[sid].get("canvas_state", {})
                components = canvas_state.get("components", [])
                components.append(new_component)
                canvas_state["components"] = components
                
                await self.update_canvas(sid, canvas_state)
        
        elif action == "remove_component":
            component_id = data.get("component_id")
            
            if sid in self.session_data:
                canvas_state = self.session_data[sid].get("canvas_state", {})
                components = canvas_state.get("components", [])
                canvas_state["components"] = [
                    c for c in components if c.get("id") != component_id
                ]
                
                await self.update_canvas(sid, canvas_state)
    
    async def broadcast_agent_thought(self, thought: Dict[str, Any], room_id: str = "default"):
        """Broadcast agent thinking process to clients"""
        await self.broadcast_to_room(
            room_id,
            "agent_thought",
            {
                "thought": thought.get("thought"),
                "confidence": thought.get("confidence"),
                "evidence": thought.get("evidence", []),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Create global connection manager
manager = ConnectionManager()


# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    user_id = auth.get("user_id", "anonymous") if auth else "anonymous"
    room_id = auth.get("room_id", "default") if auth else "default"
    await manager.connect(sid, user_id, room_id)


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    await manager.disconnect(sid)


@sio.event
async def user_input(sid, data):
    """Handle user input from chat interface"""
    await manager.handle_user_input(sid, data)


@sio.event
async def canvas_interaction(sid, data):
    """Handle canvas interaction events"""
    await manager.handle_canvas_interaction(sid, data)


@sio.event
async def join_room(sid, data):
    """Join a specific room for collaboration"""
    room_id = data.get("room_id")
    if room_id:
        await sio.enter_room(sid, room_id)
        if sid in manager.session_data:
            manager.session_data[sid]["room_id"] = room_id
        await sio.emit(
            "room_joined",
            {"room_id": room_id, "status": "success"},
            room=sid
        )


@sio.event
async def leave_room(sid, data):
    """Leave a specific room"""
    room_id = data.get("room_id")
    if room_id:
        await sio.leave_room(sid, room_id)
        await sio.emit(
            "room_left",
            {"room_id": room_id, "status": "success"},
            room=sid
        )
