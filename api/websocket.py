"""
ATO Shield v2 - WebSocket Connection Manager
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
import asyncio

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
        disconnected = []
        for analyst_id, connection in self.active_connections.items():
            try:
                await connection.send_json(alert)
            except Exception as e:
                print(f"⚠️ Failed to send to {analyst_id}: {e}")
                disconnected.append(analyst_id)
        
        # Clean up disconnected clients
        for analyst_id in disconnected:
            self.disconnect(analyst_id)

    async def broadcast_stats_update(self, stats: dict):
        """Broadcast dashboard stats update to all connected clients"""
        alert = {
            'type': 'stats_update',
            'data': stats
        }
        await self.broadcast_alert(alert)

# Global manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, analyst_id: str = "anonymous"):
    """WebSocket endpoint for dashboard real-time updates"""
    await manager.connect(websocket, analyst_id)
    try:
        # Send initial ping to confirm connection
        await websocket.send_json({'type': 'connected', 'analyst_id': analyst_id})
        
        while True:
            # Keep connection alive - wait for client ping or heartbeat
            try:
                # Use asyncio.wait_for to add timeout and detect disconnects
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Echo back pong to keep connection alive
                await websocket.send_json({'type': 'pong'})
            except asyncio.TimeoutError:
                # Send heartbeat to check if client is still connected
                try:
                    await websocket.send_json({'type': 'ping'})
                except Exception:
                    break
    except WebSocketDisconnect:
        manager.disconnect(analyst_id)
    except Exception as e:
        print(f"⚠️ WebSocket error: {e}")
        manager.disconnect(analyst_id)
