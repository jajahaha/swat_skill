"""Top SQL skills."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class TopSqlTimeSkill(QuerySkill):
    """Show top SQL by total time."""

    name = "topsql"
    description = "显示总耗时最高的SQL（需启用pg_stat_statements扩展）"
    aliases = ["topsqltime"]
    query_name = "top_sql_time"


@register_skill
class TopSqlCallsSkill(QuerySkill):
    """Show top SQL by call count."""

    name = "topsqlcalls"
    description = "显示调用次数最高的SQL（需启用pg_stat_statements扩展）"
    aliases = ["topcalls"]
    query_name = "top_sql_calls"