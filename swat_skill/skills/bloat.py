"""Bloat detection skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class BloatSkill(QuerySkill):
    """Detect table bloat."""

    name = "bloat"
    description = "检测表和索引膨胀"
    aliases = ["bloatestimate"]
    query_name = "bloat_estimate"