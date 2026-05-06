"""Lock management skills."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class LocksSkill(QuerySkill):
    """Show all database locks."""

    name = "locks"
    description = "显示所有锁信息"
    query_name = "locks_all"


@register_skill
class BlockedLocksSkill(QuerySkill):
    """Show blocked locks."""

    name = "blocked"
    description = "显示被阻塞的锁"
    aliases = ["blockedlocks"]
    query_name = "locks_blocked"


@register_skill
class BlockTreeSkill(QuerySkill):
    """Show lock blocking tree."""

    name = "blocktree"
    description = "显示锁阻塞链树状结构"
    query_name = "lock_tree"