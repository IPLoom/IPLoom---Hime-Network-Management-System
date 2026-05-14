from typing import List, Dict, Any
from fastapi import WebSocket
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.loop = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total active connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all active WebSocket connections.
        """
        if not self.active_connections:
            return

        payload = json.dumps(message)
        
        # We track failed connections to remove them after the broadcast
        failed_connections = []
        
        # Create a list of tasks for sending to each connection
        tasks = []
        for connection in self.active_connections:
            tasks.append(self._send_message(connection, payload))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if result is False or isinstance(result, Exception):
                    failed_connections.append(self.active_connections[i])
        
        # Cleanup dead connections immediately
        for dead_conn in failed_connections:
            self.disconnect(dead_conn)

    async def _send_message(self, websocket: WebSocket, payload: str) -> bool:
        try:
            await websocket.send_text(payload)
            return True
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            return False

    def broadcast_sync(self, message: Dict[str, Any]):
        """
        Thread-safe broadcast for sync callers.
        """
        if not self.active_connections:
            return
            
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)
        else:
            # Fallback to current thread loop if possible
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.broadcast(message))
            except:
                pass

# Global instance
manager = ConnectionManager()
