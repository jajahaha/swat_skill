"""Replication skills."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class ReplicationSkill(QuerySkill):
    """Show replication status."""

    name = "replication"
    description = "显示复制状态"
    aliases = ["repl", "standby"]
    query_name = "replication_status"


@register_skill
class SlotsSkill(QuerySkill):
    """Show replication slots."""

    name = "slots"
    description = "显示复制槽状态"
    query_name = "replication_slots"