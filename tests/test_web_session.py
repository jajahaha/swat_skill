"""Test WebSocket session manager."""

import pytest
import asyncio

from swat_skill.web.websocket import SessionManager
from swat_skill.config import Config


class TestSessionManager:
    """Test SessionManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SessionManager()

    def test_create_session(self):
        """Test session creation."""
        from unittest.mock import Mock

        config = Config()
        # Mock database connection to avoid actual connection
        from swat_skill.web.adapter import WebSession
        from swat_skill.database.connection import ConnectionManager

        # Create mock connection
        mock_conn = Mock(spec=ConnectionManager)
        mock_conn.is_connected.return_value = True
        mock_conn.get_server_info.return_value = {"version": "14.0", "connected": True}

        # Create session manually to avoid database connection
        session = WebSession("test-session-id", mock_conn, config)
        self.manager.sessions[session.id] = session

        assert session.id == "test-session-id"
        assert self.manager.get_active_count() == 1

    def test_remove_session(self):
        """Test session removal."""
        from unittest.mock import Mock
        from swat_skill.web.adapter import WebSession
        from swat_skill.database.connection import ConnectionManager

        config = Config()
        mock_conn = Mock(spec=ConnectionManager)
        mock_conn.disconnect = Mock()

        session = WebSession("test-id", mock_conn, config)
        self.manager.sessions[session.id] = session

        self.manager.remove_session("test-id")

        assert self.manager.get_active_count() == 0
        assert self.manager.get_session("test-id") is None

    def test_get_session(self):
        """Test getting session by ID."""
        from unittest.mock import Mock
        from swat_skill.web.adapter import WebSession
        from swat_skill.database.connection import ConnectionManager

        config = Config()
        mock_conn = Mock(spec=ConnectionManager)

        session = WebSession("test-id", mock_conn, config)
        self.manager.sessions[session.id] = session

        retrieved = self.manager.get_session("test-id")
        assert retrieved is session

    def test_get_nonexistent_session(self):
        """Test getting non-existent session."""
        session = self.manager.get_session("nonexistent")
        assert session is None

    def test_cleanup_expired(self):
        """Test cleanup of expired sessions."""
        from unittest.mock import Mock
        from datetime import datetime, timedelta
        from swat_skill.web.adapter import WebSession
        from swat_skill.database.connection import ConnectionManager

        config = Config()
        mock_conn = Mock(spec=ConnectionManager)
        mock_conn.disconnect = Mock()

        # Create expired session
        session = WebSession("expired-id", mock_conn, config)
        session.last_activity = datetime.now() - timedelta(minutes=60)
        self.manager.sessions[session.id] = session

        # Create fresh session
        fresh_session = WebSession("fresh-id", mock_conn, config)
        self.manager.sessions[fresh_session.id] = fresh_session

        # Cleanup
        count = self.manager.cleanup_expired(30)

        assert count == 1
        assert self.manager.get_session("expired-id") is None
        assert self.manager.get_session("fresh-id") is fresh_session

    def test_get_active_count(self):
        """Test getting active session count."""
        assert self.manager.get_active_count() == 0

        from unittest.mock import Mock
        from swat_skill.web.adapter import WebSession
        from swat_skill.database.connection import ConnectionManager

        config = Config()
        mock_conn = Mock(spec=ConnectionManager)

        session1 = WebSession("id1", mock_conn, config)
        session2 = WebSession("id2", mock_conn, config)
        self.manager.sessions[session1.id] = session1
        self.manager.sessions[session2.id] = session2

        assert self.manager.get_active_count() == 2

    @pytest.mark.asyncio
    async def test_cleanup_task(self):
        """Test cleanup task can be started and stopped."""
        await self.manager.start_cleanup_task()
        assert self.manager._cleanup_task is not None

        await self.manager.stop_cleanup_task()
        # After stop, task should be cancelled (not None)
        assert self.manager._cleanup_task is not None
        assert self.manager._cleanup_task.cancelled() is True