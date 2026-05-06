"""Skill base class and registry.

Provides the foundation for all swat_skill diagnostic skills.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from ..database.connection import ConnectionManager, QueryResult
from ..utils.formatter import Formatter, HealthItem


@dataclass
class SkillResult:
    """Result of a skill execution."""

    success: bool
    data: Any  # Can be list of dicts, health items, or other types
    message: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    result_type: str = "table"  # "table", "health", "text", "sql"


class Skill(ABC):
    """Abstract base class for all skills."""

    name: str = ""
    description: str = ""
    aliases: List[str] = []
    params: List[str] = []

    @abstractmethod
    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute the skill.

        Args:
            conn: Database connection manager.
            args: Skill arguments (from user input).
            formatter: Output formatter.

        Returns:
            SkillResult with execution data and metadata.
        """
        pass

    def help(self) -> str:
        """Get skill help text."""
        help_text = f"/{self.name} - {self.description}"
        if self.params:
            help_text += f"\n  Parameters: {', '.join(self.params)}"
        return help_text


class QuerySkill(Skill):
    """Skill that executes a predefined SQL query."""

    query_name: str = ""

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute predefined query and return results."""
        from ..database.queries import get_query

        sql = get_query(self.query_name)
        if not sql:
            return SkillResult(
                success=False,
                data=None,
                error=f"Query '{self.query_name}' not found",
            )

        result = conn.execute(sql)
        return SkillResult(
            success=result.success,
            data=result.rows,
            error=result.error,
            execution_time=result.execution_time,
            result_type="table",
        )


class SkillRegistry:
    """Registry for all available skills."""

    _skills: Dict[str, Type[Skill]] = {}

    @classmethod
    def register(cls, skill_class: Type[Skill]) -> None:
        """Register a skill class."""
        if not skill_class.name:
            raise ValueError(f"Skill class must have a name attribute")

        cls._skills[skill_class.name] = skill_class

        # Also register aliases
        for alias in skill_class.aliases:
            cls._skills[alias] = skill_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[Skill]]:
        """Get a skill class by name."""
        return cls._skills.get(name)

    @classmethod
    def list(cls) -> List[Type[Skill]]:
        """List all registered skill classes."""
        # Return unique skills (excluding aliases)
        unique_skills = {}
        for name, skill_class in cls._skills.items():
            if skill_class.name not in unique_skills:
                unique_skills[skill_class.name] = skill_class
        return list(unique_skills.values())

    @classmethod
    def get_help_text(cls) -> str:
        """Get help text for all skills."""
        lines = ["Available skills:"]
        for skill_class in cls.list():
            skill = skill_class()
            lines.append(f"  {skill.help()}")
        return "\n".join(lines)

    @classmethod
    def create_skill(cls, name: str) -> Optional[Skill]:
        """Create a skill instance by name."""
        skill_class = cls.get(name)
        if skill_class:
            return skill_class()
        return None


def register_skill(skill_class: Type[Skill]) -> Type[Skill]:
    """Decorator to register a skill class."""
    SkillRegistry.register(skill_class)
    return skill_class