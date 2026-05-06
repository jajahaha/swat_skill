"""LLM diagnostic skill."""

from typing import List

from ..config import Config
from ..database.connection import ConnectionManager
from .base import Skill, SkillResult, register_skill
from ..utils.formatter import Formatter


@register_skill
class LlmSkill(Skill):
    """LLM-powered diagnostics."""

    name = "llm"
    description = "使用LLM进行智能诊断"
    aliases = ["ai", "chat"]

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
        """Execute LLM diagnosis."""
        # This is a placeholder - actual LLM integration is in llm/agent.py
        if not self.config or not self.config.llm.get_api_key():
            return SkillResult(
                success=False,
                data=None,
                error="LLM not configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.",
            )

        # If args provided, use them as question
        question = " ".join(args) if args else "请分析数据库当前状态并给出诊断报告"

        return SkillResult(
            success=True,
            data={"question": question, "needs_llm": True},
            result_type="llm",
        )