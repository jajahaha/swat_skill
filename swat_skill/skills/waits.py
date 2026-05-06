"""Wait events skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class WaitsSkill(QuerySkill):
    """Show wait events statistics."""

    name = "waits"
    description = "显示等待事件统计"
    query_name = "wait_events"