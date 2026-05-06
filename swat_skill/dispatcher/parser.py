"""Input parser for distinguishing input types."""

from .base import Skill, SkillResult, register_skill


@register_skill
class ParserSkill(Skill):
    """Parse user input."""

    name = "parse"
    description = "解析用户输入"

    def execute(self, conn, args, formatter):
        """Parse input."""
        pass