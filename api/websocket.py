"""
ATO Shield v2 - WebSocket Connection Manager
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections for dashboard clients"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, analyst_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[analyst_id] = websocket
    
    def disconnect(self, analyst_id: str):
        """Remove WebSocket connection"""
        if analyst_id in self.active_connections:
            del self.active_connections[analyst_id]
    
    async def send_alert(self, analyst_id: str, alert: dict):
        """Send alert to specific analyst"""
        if analyst_id in self.active_connections:
            await self.active_connections[analyst_id].send_json(alert)
    
    async def broadcast_alert(self, alert: dict):
        """Broadcast alert to all connected analysts"""
        for connection in self.active_connections.values():
            try:
                await connection.send_json(alert)
            except Exception:
                pass

# Global manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, analyst_id: str = "anonymous"):
    """WebSocket endpoint for dashboard real-time updates"""
    await manager.connect(websocket, analyst_id)
    try:
        while True:
            # Keep connection alive - client doesn't send messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(analyst_id)
