"""
WebSocket connection manager for streaming workflow execution logs.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio


class ConnectionManager:
    """
    Manages WebSocket connections for real-time log streaming.
    
    Allows multiple clients to connect to the same workflow run
    and receive execution updates in real-time.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, run_id: str, websocket: WebSocket):
        """
        Accept a new WebSocket connection for a specific run.
        
        Args:
            run_id: Workflow run ID
            websocket: WebSocket connection
        """
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = set()
        self.active_connections[run_id].add(websocket)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "run_id": run_id,
            "message": f"Connected to workflow run {run_id}"
        })
    
    def disconnect(self, run_id: str, websocket: WebSocket):
        """
        Remove a WebSocket connection.
        
        Args:
            run_id: Workflow run ID
            websocket: WebSocket connection to remove
        """
        if run_id in self.active_connections:
            self.active_connections[run_id].discard(websocket)
            # Clean up empty sets
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]
    
    async def send_log(self, run_id: str, message: dict):
        """
        Send a log message to all connected clients for a run.
        
        Args:
            run_id: Workflow run ID
            message: Log message dictionary
        """
        if run_id in self.active_connections:
            # Send to all connected clients
            disconnected = set()
            for connection in self.active_connections[run_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Mark for removal if send fails
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for connection in disconnected:
                self.disconnect(run_id, connection)
    
    def get_connection_count(self, run_id: str) -> int:
        """
        Get number of active connections for a run.
        
        Args:
            run_id: Workflow run ID
            
        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(run_id, set()))


# Global connection manager instance
manager = ConnectionManager()
