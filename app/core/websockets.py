# app/core/websockets.py
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        # Maps lead_id to a list of active WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, lead_id: str):
        await websocket.accept()
        if lead_id not in self.active_connections:
            self.active_connections[lead_id] = []
        self.active_connections[lead_id].append(websocket)

    def disconnect(self, websocket: WebSocket, lead_id: str):
        if lead_id in self.active_connections:
            self.active_connections[lead_id].remove(websocket)
            if not self.active_connections[lead_id]:
                del self.active_connections[lead_id]

    async def broadcast_lead_update(self, lead_id: str, message: dict):
        if lead_id in self.active_connections:
            for connection in self.active_connections[lead_id]:
                await connection.send_json(message)

manager = ConnectionManager()