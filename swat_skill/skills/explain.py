"""Explain SQL skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import Skill, SkillResult, register_skill
from ..utils.formatter import Formatter


@register_skill
class ExplainSkill(Skill):
    """Show SQL execution plan."""

    name = "explain"
    description = "显示SQL执行计划"
    aliases = ["plan"]

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute EXPLAIN ANALYZE."""
        if not args:
            return SkillResult(
                success=False,
                data=None,
                error="No SQL provided. Usage: /explain <query>",
            )

        # Join args as SQL
        sql = " ".join(args)

        # Add EXPLAIN ANALYZE if not already present
        if not sql.upper().startswith("EXPLAIN"):
            sql = f"EXPLAIN ANALYZE {sql}"

        result = conn.execute(sql)
        return SkillResult(
            success=result.success,
            data=result.rows,
            error=result.error,
            execution_time=result.execution_time,
            result_type="table",
        )