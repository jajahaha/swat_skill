"""Space analysis skills."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class SpaceSkill(QuerySkill):
    """Show database space usage."""

    name = "space"
    description = "显示数据库空间使用"
    query_name = "database_size"


@register_skill
class TableSizesSkill(QuerySkill):
    """Show table sizes."""

    name = "tablesizes"
    description = "显示大表空间占用"
    aliases = ["segments", "tables"]
    query_name = "table_sizes"


@register_skill
class IndexSizesSkill(QuerySkill):
    """Show index sizes."""

    name = "indexsizes"
    description = "显示索引空间占用"
    aliases = ["indexes"]
    query_name = "index_sizes"