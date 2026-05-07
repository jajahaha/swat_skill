"""Test Web Interface adapter."""

import pytest
from unittest.mock import Mock

from swat_skill.web.adapter import WebFormatter, WebSession
from swat_skill.skills.base import SkillResult
from swat_skill.utils.formatter import HealthItem


class TestWebFormatter:
    """Test WebFormatter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = WebFormatter()

    def test_format_table_with_data(self):
        """Test table formatting with data."""
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = self.formatter.format_table(data, execution_time=0.5)

        assert result["type"] == "table"
        assert result["columns"] == ["name", "age"]
        assert result["row_count"] == 2
        assert result["rows"] == data
        assert result["execution_time"] == 0.5

    def test_format_table_empty(self):
        """Test table formatting with empty data."""
        result = self.formatter.format_table([])

        assert result["type"] == "table"
        assert result["rows"] == []
        assert result["row_count"] == 0

    def test_format_table_custom_columns(self):
        """Test table formatting with custom columns."""
        data = [{"a": 1, "b": 2, "c": 3}]
        result = self.formatter.format_table(data, columns=["a", "c"])

        assert result["columns"] == ["a", "c"]

    def test_format_health_report(self):
        """Test health report formatting."""
        items = [
            HealthItem(category="Connections", name="Total", value="10", status="ok"),
            HealthItem(category="Connections", name="Active", value="5", status="ok"),
            HealthItem(category="Locks", name="Blocked", value="2", status="warning"),
        ]
        result = self.formatter.format_health_report(items, overall_status="ok")

        assert result["type"] == "health"
        assert result["overall"] == "ok"
        assert len(result["items"]) == 3
        assert result["items"][0]["category"] == "Connections"

    def test_format_error(self):
        """Test error formatting."""
        result = self.formatter.format_error("Test error message")

        assert result["type"] == "error"
        assert result["message"] == "Test error message"

    def test_format_success(self):
        """Test success formatting."""
        result = self.formatter.format_success("Operation completed")

        assert result["type"] == "success"
        assert result["message"] == "Operation completed"

    def test_format_info(self):
        """Test info formatting."""
        result = self.formatter.format_info("Information message")

        assert result["type"] == "info"
        assert result["message"] == "Information message"

    def test_format_text(self):
        """Test text formatting."""
        result = self.formatter.format_text("Plain text content")

        assert result["type"] == "text"
        assert result["content"] == "Plain text content"

    def test_format_empty(self):
        """Test empty formatting."""
        result = self.formatter.format_empty()

        assert result["type"] == "empty"

    def test_format_exit(self):
        """Test exit formatting."""
        result = self.formatter.format_exit("Goodbye!")

        assert result["type"] == "exit"
        assert result["message"] == "Goodbye!"

    def test_format_llm_step(self):
        """Test LLM step formatting."""
        result = self.formatter.format_llm_step("thinking", "Analyzing...")

        assert result["type"] == "llm_step"
        assert result["step"] == "thinking"
        assert result["content"] == "Analyzing..."


class TestWebSession:
    """Test WebSession class."""

    def test_is_expired_false(self):
        """Test session not expired."""
        from datetime import datetime, timedelta
        from swat_skill.config import Config
        from swat_skill.database.connection import ConnectionManager

        # Mock session
        config = Config()
        conn = Mock(spec=ConnectionManager)
        session = WebSession("test-id", conn, config)

        # Fresh session should not be expired
        assert session.is_expired(30) is False

    def test_is_expired_true(self):
        """Test session expired."""
        from datetime import datetime, timedelta
        from swat_skill.config import Config
        from swat_skill.database.connection import ConnectionManager

        config = Config()
        conn = Mock(spec=ConnectionManager)
        session = WebSession("test-id", conn, config)

        # Manually set last_activity to past
        session.last_activity = datetime.now() - timedelta(minutes=60)

        assert session.is_expired(30) is True