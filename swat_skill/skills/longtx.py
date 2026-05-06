"""Long transaction skills."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class LongTxSkill(QuerySkill):
    """Show long transactions."""

    name = "longtx"
    description = "显示超过60秒的长事务"
    query_name = "long_transactions"


@register_skill
class IdleTxSkill(QuerySkill):
    """Show idle in transaction sessions."""

    name = "idletx"
    description = "显示idle in transaction超过5分钟的会话"
    aliases = ["idle"]
    query_name = "idle_in_transaction"