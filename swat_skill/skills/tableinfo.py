"""Table info skills."""

from typing import List

from ..database.connection import ConnectionManager
from ..database.queries import get_query
from .base import Skill, SkillResult, QuerySkill, register_skill
from ..utils.formatter import Formatter


@register_skill
class TableInfoSkill(Skill):
    """Show table structure info."""

    name = "tableinfo"
    description = "显示表结构信息"
    aliases = ["desc", "describe"]

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute table info query."""
        if not args:
            # Show all tables
            sql = get_query("table_info")
        else:
            # Show specific table
            table_name = args[0]
            # Parse schema.table format
            if "." in table_name:
                schema, table = table_name.split(".", 1)
            else:
                schema = "public"
                table = table_name

            sql = f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = '{schema}' AND table_name = '{table}'
                ORDER BY ordinal_position
            """

        result = conn.execute(sql)
        return SkillResult(
            success=result.success,
            data=result.rows,
            error=result.error,
            execution_time=result.execution_time,
            result_type="table",
        )


@register_skill
class TableIndexesSkill(QuerySkill):
    """Show table indexes."""

    name = "tableindexes"
    description = "显示表的索引信息"
    aliases = ["indexes"]
    query_name = "table_indexes"