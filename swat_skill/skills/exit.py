"""Exit skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import Skill, SkillResult, register_skill
from ..utils.formatter import Formatter


@register_skill
class ExitSkill(Skill):
    """Exit the CLI."""

    name = "exit"
    description = "退出程序"
    aliases = ["quit", "q"]

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Return exit signal."""
        return SkillResult(
            success=True,
            data=None,
            message="Goodbye!",
            result_type="exit",
        )