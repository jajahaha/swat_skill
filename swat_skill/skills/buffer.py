"""Buffer stats skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class BufferStatsSkill(QuerySkill):
    """Show buffer statistics."""

    name = "buffers"
    description = "显示缓存命中率统计"
    aliases = ["sharedbuffs", "cache"]
    query_name = "buffer_stats"