"""Test skill registry and base classes."""

import pytest

from swat_skill.skills.base import (
    Skill,
    SkillResult,
    SkillRegistry,
    QuerySkill,
    register_skill,
)
from swat_skill.skills import (
    HealthSkill,
    HelpSkill,
    SessionsSkill,
    LocksSkill,
)


class TestSkillResult:
    """Test SkillResult dataclass."""

    def test_success_result(self):
        """Test successful result."""
        result = SkillResult(
            success=True,
            data=[{"col1": "val1"}],
            result_type="table",
        )
        assert result.success is True
        assert result.error is None

    def test_error_result(self):
        """Test error result."""
        result = SkillResult(
            success=False,
            data=None,
            error="Test error",
        )
        assert result.success is False
        assert result.error == "Test error"


class TestSkillRegistry:
    """Test SkillRegistry functionality."""

    def test_get_existing_skill(self):
        """Test getting an existing skill."""
        skill_class = SkillRegistry.get("health")
        assert skill_class is not None
        assert skill_class.name == "health"

    def test_get_nonexistent_skill(self):
        """Test getting a non-existent skill."""
        skill_class = SkillRegistry.get("nonexistent")
        assert skill_class is None

    def test_list_skills(self):
        """Test listing all skills."""
        skills = SkillRegistry.list()
        assert len(skills) > 0
        # Should contain known skills
        skill_names = [s.name for s in skills]
        assert "health" in skill_names
        assert "help" in skill_names

    def test_get_help_text(self):
        """Test getting help text."""
        help_text = SkillRegistry.get_help_text()
        assert "Available skills:" in help_text
        assert "/health" in help_text

    def test_skill_aliases(self):
        """Test skill aliases."""
        # Help skill has alias "?"
        skill_class = SkillRegistry.get("?")
        assert skill_class is not None
        assert skill_class.name == "help"


class TestSkillBase:
    """Test Skill base class."""

    def test_help_method(self):
        """Test skill help method."""
        skill = HealthSkill()
        help_text = skill.help()
        assert "/health" in help_text

    def test_skill_attributes(self):
        """Test skill attributes."""
        skill = HelpSkill()
        assert skill.name == "help"
        assert skill.description == "显示所有可用命令"


class TestQuerySkill:
    """Test QuerySkill base class."""

    def test_query_skill_instantiation(self):
        """Test QuerySkill can be instantiated."""
        # SessionsSkill is a QuerySkill
        skill = SessionsSkill()
        assert skill.query_name == "sessions_all"


class TestRegisterDecorator:
    """Test register_skill decorator."""

    def test_decorator_registers_skill(self):
        """Test that decorator registers skill properly."""
        @register_skill
        class TestSkill(Skill):
            name = "test_skill"
            description = "Test skill"

            def execute(self, conn, args, formatter):
                return SkillResult(success=True, data=None)

        # Should be registered
        registered = SkillRegistry.get("test_skill")
        assert registered is not None
        assert registered.name == "test_skill"