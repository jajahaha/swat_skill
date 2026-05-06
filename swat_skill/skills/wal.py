"""WAL status skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class WalSkill(QuerySkill):
    """Show WAL status."""

    name = "wal"
    description = "显示WAL日志状态"
    aliases = ["walstatus"]
    query_name = "wal_status"