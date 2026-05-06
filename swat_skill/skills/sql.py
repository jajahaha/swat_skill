"""Execute SQL skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import Skill, SkillResult, register_skill
from ..utils.formatter import Formatter


@register_skill
class SqlSkill(Skill):
    """Execute arbitrary SQL."""

    name = "sql"
    description = "执行自定义SQL语句"
    aliases = []

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute SQL from args."""
        if not args:
            return SkillResult(
                success=False,
                data=None,
                error="No SQL provided. Usage: /sql <query>",
            )

        # Join args as SQL
        sql = " ".join(args)

        result = conn.execute(sql)
        return SkillResult(
            success=result.success,
            data=result.rows,
            error=result.error,
            execution_time=result.execution_time,
            result_type="table",
        )