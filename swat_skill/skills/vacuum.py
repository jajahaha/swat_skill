"""Vacuum status skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class VacuumSkill(QuerySkill):
    """Show vacuum status."""

    name = "vacuum"
    description = "显示Vacuum状态和需要清理的表"
    aliases = ["vacuumstatus"]
    query_name = "vacuum_status"