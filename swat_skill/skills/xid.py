"""XID age skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class XidAgeSkill(QuerySkill):
    """Show XID wraparound status."""

    name = "xid"
    description = "显示事务ID使用情况（wraparound监控）"
    aliases = ["xidage", "wraparound"]
    query_name = "xid_age"