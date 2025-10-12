from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str):
    await manager.connect(workspace_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Echo back for now
            await manager.broadcast(workspace_id, {
                "type": "message",
                "data": data
            })
    except WebSocketDisconnect:
        await manager.disconnect(workspace_id, websocket)
