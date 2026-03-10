"""WebSocket handler for real-time updates"""
import json
import asyncio
import logging
from typing import List, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_sensor_update(self, reading_data: dict):
        """Broadcast sensor reading update"""
        message = {
            "type": "sensor_update",
            "data": reading_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_alert(self, alert_data: dict):
        """Broadcast new alert"""
        message = {
            "type": "alert",
            "data": alert_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_bin_update(self, bin_data: dict):
        """Broadcast bin status update"""
        message = {
            "type": "bin_update",
            "data": bin_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)


# Global connection manager instance
manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket):
    """Handle WebSocket connection"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive and process client messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                if message_type == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
                
                elif message_type == "subscribe":
                    # Client subscribing to specific updates
                    channel = message.get("channel", "all")
                    await manager.send_personal_message({
                        "type": "subscribed",
                        "channel": channel
                    }, websocket)
                
                else:
                    # Echo back unknown messages
                    await manager.send_personal_message({
                        "type": "echo",
                        "received": message
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON"
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
