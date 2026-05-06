"""Slow SQL skill."""

from typing import List

from ..database.connection import ConnectionManager
from ..database.queries import get_query
from ..utils.formatter import Formatter
from .base import Skill, SkillResult, register_skill


@register_skill
class SlowSqlSkill(Skill):
    """Find slow SQL statements."""

    name = "slowsql"
    description = "查找慢SQL（需启用pg_stat_statements扩展）"
    aliases = []

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute slow SQL search."""
        # Get threshold from args (default 1000ms)
        threshold_ms = 1000
        if args:
            try:
                threshold_ms = int(args[0])
            except ValueError:
                pass

        # Note: pg_stat_statements may not be installed
        sql = get_query("slow_sql")
        if not sql:
            return SkillResult(
                success=False,
                data=None,
                error="Slow SQL query not found",
            )

        result = conn.execute(sql)

        if not result.success:
            return SkillResult(
                success=False,
                data=None,
                error=f"Query failed: {result.error}",
            )

        # Filter by threshold
        filtered_rows = [
            row for row in result.rows
            if float(row.get("mean_time_ms", 0)) >= threshold_ms
        ]

        return SkillResult(
            success=True,
            data=filtered_rows,
            execution_time=result.execution_time,
            result_type="table",
        )