"""Web interface module for swat_skill.

Provides FastAPI-based web interface with WebSocket for real-time interaction.
"""

from .adapter import WebFormatter, WebSession
from .websocket import SessionManager

__all__ = ["WebFormatter", "WebSession", "SessionManager"]