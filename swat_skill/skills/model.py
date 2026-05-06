"""Model management skill."""

from typing import List

from ..config import Config
from ..database.connection import ConnectionManager
from .base import Skill, SkillResult, register_skill
from ..utils.formatter import Formatter


@register_skill
class ModelSkill(Skill):
    """Manage LLM model settings."""

    name = "model"
    description = "切换或显示LLM模型"
    aliases = []

    def __init__(self, config: Config = None):
        self.config = config

    def set_config(self, config: Config) -> None:
        """Set configuration reference."""
        self.config = config

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute model management."""
        if not args:
            # Show current model
            if self.config:
                current_model = self.config.llm.model
                current_provider = self.config.llm.provider
                return SkillResult(
                    success=True,
                    data=f"Current model: {current_provider}/{current_model}",
                    result_type="text",
                )
            else:
                return SkillResult(
                    success=True,
                    data="LLM not configured",
                    result_type="text",
                )

        # Switch model
        new_model = args[0]
        if self.config:
            self.config.llm.model = new_model
            return SkillResult(
                success=True,
                data=f"Model switched to: {new_model}",
                result_type="text",
            )
        else:
            return SkillResult(
                success=False,
                data=None,
                error="Configuration not available",
            )