from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        # workspace_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, workspace_id: str, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = []
        self.active_connections[workspace_id].append(websocket)
    
    async def disconnect(self, workspace_id: str, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if workspace_id in self.active_connections:
            self.active_connections[workspace_id].remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_text(message)
    
    async def broadcast(self, workspace_id: str, message: dict):
        """Broadcast message to all clients in workspace"""
        if workspace_id in self.active_connections:
            for connection in self.active_connections[workspace_id]:
                await connection.send_json(message)
