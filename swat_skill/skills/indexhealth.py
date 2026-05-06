"""Index health skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class UnusedIndexesSkill(QuerySkill):
    """Find unused indexes."""

    name = "unusedindexes"
    description = "显示未使用的索引"
    aliases = ["unused"]
    query_name = "unused_indexes"