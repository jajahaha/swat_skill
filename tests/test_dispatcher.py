"""Test dispatcher functionality."""

import pytest
from unittest.mock import Mock, MagicMock

from swat_skill.dispatcher.router import Dispatcher
from swat_skill.dispatcher.parser import is_sql_statement
from swat_skill.skills.base import SkillResult
from swat_skill.config import Config


class TestSQLDetection:
    """Test SQL statement detection."""

    def test_select_statement(self):
        """Test SELECT statement detection."""
        assert is_sql_statement("SELECT * FROM table") is True
        assert is_sql_statement("select id from users") is True

    def test_insert_statement(self):
        """Test INSERT statement detection."""
        assert is_sql_statement("INSERT INTO table VALUES (1)") is True

    def test_update_statement(self):
        """Test UPDATE statement detection."""
        assert is_sql_statement("UPDATE table SET col=1") is True

    def test_delete_statement(self):
        """Test DELETE statement detection."""
        assert is_sql_statement("DELETE FROM table") is True

    def test_non_sql_statement(self):
        """Test non-SQL statement detection."""
        assert is_sql_statement("hello world") is False
        assert is_sql_statement("database is slow") is False
        assert is_sql_statement("/health") is False

    def test_sql_with_whitespace(self):
        """Test SQL with leading whitespace."""
        assert is_sql_statement("  SELECT * FROM table") is True
        assert is_sql_statement("\n\tselect * from users") is True


class TestDispatcher:
    """Test Dispatcher class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.conn = Mock()
        self.config = Config()
        self.formatter = Mock()
        self.dispatcher = Dispatcher(self.conn, self.config, self.formatter)

    def test_empty_input(self):
        """Test empty input handling."""
        result, skill = self.dispatcher.dispatch("")
        assert result.result_type == "empty"

    def test_whitespace_only_input(self):
        """Test whitespace only input."""
        result, skill = self.dispatcher.dispatch("   ")
        assert result.result_type == "empty"

    def test_skill_command(self):
        """Test skill command routing."""
        # Mock the connection execute method
        self.conn.execute = Mock(return_value=Mock(
            success=True,
            rows=[],
            rowcount=0,
            columns=[],
            execution_time=0.1,
        ))

        result, skill = self.dispatcher.dispatch("/help")
        assert result.success is True
        assert result.result_type == "text"

    def test_unknown_skill_command(self):
        """Test unknown skill command."""
        result, skill = self.dispatcher.dispatch("/unknownskill")
        assert result.success is False
        assert "Unknown skill" in result.error

    def test_sql_routing(self):
        """Test SQL statement routing."""
        self.conn.execute = Mock(return_value=Mock(
            success=True,
            rows=[{"id": 1}],
            rowcount=1,
            columns=["id"],
            execution_time=0.05,
        ))

        result, skill = self.dispatcher.dispatch("SELECT 1")
        assert result.result_type == "table"
        assert result.success is True

    def test_sql_error(self):
        """Test SQL execution error."""
        self.conn.execute = Mock(return_value=Mock(
            success=False,
            rows=[],
            rowcount=0,
            columns=[],
            execution_time=0.0,
            error="Syntax error",
        ))

        result, skill = self.dispatcher.dispatch("SELECT invalid")
        assert result.success is False
        assert result.error == "Syntax error"

    def test_get_skill_names(self):
        """Test getting skill names."""
        names = self.dispatcher.get_skill_names()
        assert len(names) > 0
        assert "health" in names
        assert "help" in names