"""Input dispatcher for routing user input to appropriate handlers.

Routes input to three handlers:
1. Skill commands (/command)
2. SQL statements
3. Natural language (LLM)
"""

from typing import Optional, Tuple

from ..config import Config
from ..database.connection import ConnectionManager
from ..database.queries import is_sql_statement
from ..skills.base import Skill, SkillRegistry, SkillResult
from ..utils.formatter import Formatter


class Dispatcher:
    """Routes user input to appropriate handlers."""

    def __init__(
        self,
        conn: ConnectionManager,
        config: Config,
        formatter: Formatter,
    ):
        self.conn = conn
        self.config = config
        self.formatter = formatter

    def dispatch(self, input: str) -> Tuple[SkillResult, Optional[Skill]]:
        """Dispatch input to appropriate handler.

        Returns tuple of (result, skill) where skill is the executed skill instance.
        """
        input = input.strip()

        if not input:
            return SkillResult(success=True, data=None, result_type="empty"), None

        # 1. Check for skill command (/command)
        if input.startswith("/"):
            return self._handle_skill(input)

        # 2. Check for SQL statement
        if is_sql_statement(input):
            return self._handle_sql(input)

        # 3. Handle as natural language (LLM)
        return self._handle_natural_language(input)

    def _handle_skill(self, input: str) -> Tuple[SkillResult, Optional[Skill]]:
        """Handle /command input."""
        # Parse skill name and arguments
        parts = input[1:].split()  # Remove leading /
        skill_name = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        # Get skill from registry
        skill_class = SkillRegistry.get(skill_name)
        if not skill_class:
            return SkillResult(
                success=False,
                data=None,
                error=f"Unknown skill: {skill_name}. Type /help for available commands.",
            ), None

        # Create skill instance
        skill = skill_class()

        # Set config for skills that need it (model, llm)
        if hasattr(skill, "set_config"):
            skill.set_config(self.config)

        # Execute skill
        result = skill.execute(self.conn, args, self.formatter)
        return result, skill

    def _handle_sql(self, input: str) -> Tuple[SkillResult, Optional[Skill]]:
        """Handle SQL input."""
        result = self.conn.execute(input)
        return SkillResult(
            success=result.success,
            data=result.rows,
            error=result.error,
            execution_time=result.execution_time,
            result_type="table",
        ), None

    def _handle_natural_language(self, input: str) -> Tuple[SkillResult, Optional[Skill]]:
        """Handle natural language input via LLM."""
        # Get LLM skill
        skill_class = SkillRegistry.get("llm")
        if not skill_class:
            return SkillResult(
                success=False,
                data=None,
                error="LLM skill not available",
            ), None

        skill = skill_class()
        skill.set_config(self.config)

        # Pass the question as args
        result = skill.execute(self.conn, [input], self.formatter)
        return result, skill

    def get_skill_names(self) -> list:
        """Get list of all skill names."""
        return list(SkillRegistry._skills.keys())