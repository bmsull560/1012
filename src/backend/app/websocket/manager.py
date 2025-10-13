import asyncio
import time
from typing import Dict, List

from fastapi import WebSocket

class ConnectionManager:
    """Manages WebSocket connections, broadcasting, and cleanup."""

    def __init__(self, timeout_seconds: int = 300):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.last_seen: Dict[WebSocket, float] = {}
        self.timeout_seconds = timeout_seconds

    async def connect(self, workspace_id: str, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = []
        self.active_connections[workspace_id].append(websocket)
        self.last_seen[websocket] = time.time()

    def disconnect(self, workspace_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if workspace_id in self.active_connections:
            if websocket in self.active_connections[workspace_id]:
                self.active_connections[workspace_id].remove(websocket)
        self.last_seen.pop(websocket, None)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_text(message)
    
    async def broadcast(self, workspace_id: str, message: dict):
        """Broadcast message to all clients in a workspace."""
        if workspace_id in self.active_connections:
            for connection in self.active_connections[workspace_id]:
                self.last_seen[connection] = time.time()
                await connection.send_json(message)

    async def cleanup_stale_connections(self):
        """Periodically check for and remove stale connections."""
        while True:
            await asyncio.sleep(60)  # Check every 60 seconds
            now = time.time()
            stale_connections = []
            for workspace_id, connections in self.active_connections.items():
                for connection in connections:
                    if now - self.last_seen.get(connection, now) > self.timeout_seconds:
                        stale_connections.append((workspace_id, connection))
            
            for workspace_id, connection in stale_connections:
                try:
                    await connection.close()
                except RuntimeError:
                    pass  # Connection already closed
                self.disconnect(workspace_id, connection)
                print(f"Cleaned up stale connection in workspace {workspace_id}")
