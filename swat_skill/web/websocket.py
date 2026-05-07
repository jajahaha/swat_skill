"""WebSocket handler for real-time command execution.

Manages WebSocket connections and command dispatch for web interface.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect

from ..config import Config, load_config
from ..skills.base import SkillRegistry
from .adapter import WebSession, create_web_session


class SessionManager:
    """Manages active web sessions."""

    def __init__(self):
        self.sessions: Dict[str, WebSession] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_task(self) -> None:
        """Stop cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self) -> None:
        """Periodically cleanup expired sessions."""
        while True:
            await asyncio.sleep(60)  # Check every minute
            self.cleanup_expired()

    def cleanup_expired(self, max_age_minutes: int = 30) -> int:
        """Remove expired sessions."""
        expired = []
        for session_id, session in self.sessions.items():
            if session.is_expired(max_age_minutes):
                expired.append(session_id)

        for session_id in expired:
            session = self.sessions.pop(session_id, None)
            if session:
                session.disconnect()

        return len(expired)

    def create_session(self, config: Config) -> WebSession:
        """Create new session."""
        session = create_web_session(config)
        self.sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[WebSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def remove_session(self, session_id: str) -> None:
        """Remove session."""
        session = self.sessions.pop(session_id, None)
        if session:
            session.disconnect()

    def get_active_count(self) -> int:
        """Get number of active sessions."""
        return len(self.sessions)


# Global session manager
session_manager = SessionManager()


async def handle_websocket(websocket: WebSocket, session_id: Optional[str] = None):
    """Handle WebSocket connection.

    Args:
        websocket: WebSocket connection.
        session_id: Optional existing session ID.
    """
    await websocket.accept()

    # Load config
    config = load_config()

    session = None

    try:
        # Create or get session
        if session_id:
            session = session_manager.get_session(session_id)
            if not session:
                # Create new session if ID not found
                session = session_manager.create_session(config)
        else:
            session = session_manager.create_session(config)

        # Send session info
        server_info = session.get_server_info()
        skill_names = [f"/{s.name}" for s in SkillRegistry.list()]
        await websocket.send_json({
            "type": "connected",
            "session_id": session.id,
            "server_info": server_info,
            "skill_names": skill_names,
        })

        while True:
            try:
                # Receive command from client
                data = await websocket.receive_json()
                command = data.get("command", "")

                if not command.strip():
                    continue

                # Check for exit command
                if command.strip().lower() in ("/exit", "/quit"):
                    await websocket.send_json({
                        "type": "exit",
                        "message": "Goodbye!",
                    })
                    break

                # Dispatch command (wrap in try to catch execution errors)
                try:
                    result = session.dispatch(command)
                except Exception as e:
                    result = {"type": "error", "message": f"Execution error: {str(e)}"}

                # Send result
                await websocket.send_json(result)

                # Check if result indicates exit
                if result.get("type") == "exit":
                    break

            except json.JSONDecodeError:
                # Invalid JSON from client - send error but continue
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format",
                })
                continue

            except WebSocketDisconnect:
                # Client disconnected - exit loop
                break

    except WebSocketDisconnect:
        # Client disconnected during setup
        pass

    except Exception as e:
        # Setup error (database connection, etc.)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Session error: {str(e)}",
            })
        except Exception:
            pass  # WebSocket may already be closed

    finally:
        # Cleanup session on disconnect
        if session:
            session_manager.remove_session(session.id)


async def handle_command_http(session_id: str, command: str) -> Dict:
    """Handle command via HTTP API.

    Args:
        session_id: Session ID.
        command: Command to execute.

    Returns:
        JSON result.
    """
    session = session_manager.get_session(session_id)
    if not session:
        return {"type": "error", "message": "Session not found"}

    return session.dispatch(command)