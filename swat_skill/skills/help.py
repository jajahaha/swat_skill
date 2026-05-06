"""Help skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import Skill, SkillRegistry, SkillResult, register_skill
from ..utils.formatter import Formatter


@register_skill
class HelpSkill(Skill):
    """Show help for all skills."""

    name = "help"
    description = "显示所有可用命令"
    aliases = ["?"]

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Return help text."""
        if args:
            # Show help for specific skill
            skill_name = args[0]
            skill_class = SkillRegistry.get(skill_name)
            if skill_class:
                skill = skill_class()
                return SkillResult(
                    success=True,
                    data=skill.help(),
                    result_type="text",
                )
            else:
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"Unknown skill: {skill_name}",
                )

        # Show all skills
        return SkillResult(
            success=True,
            data=SkillRegistry.get_help_text(),
            result_type="text",
        )