"""Database parameters skill."""

from typing import List

from ..database.connection import ConnectionManager
from ..database.queries import get_query
from .base import Skill, SkillResult, QuerySkill, register_skill
from ..utils.formatter import Formatter


@register_skill
class ParamsSkill(Skill):
    """Search and show database parameters."""

    name = "params"
    description = "搜索和显示数据库参数"
    aliases = ["settings"]

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute parameter search."""
        if args:
            # Search for specific parameter
            pattern = args[0]
            sql = f"""
                SELECT name, setting, unit, source, short_desc
                FROM pg_settings
                WHERE name LIKE '%{pattern}%'
                ORDER BY name
            """
        else:
            sql = get_query("params_all")

        result = conn.execute(sql)
        return SkillResult(
            success=result.success,
            data=result.rows,
            error=result.error,
            execution_time=result.execution_time,
            result_type="table",
        )


@register_skill
class MemoryParamsSkill(QuerySkill):
    """Show memory-related parameters."""

    name = "memory"
    description = "显示内存相关参数"
    query_name = "params_memory"