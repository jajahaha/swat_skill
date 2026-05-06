"""Session management skills."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class SessionsSkill(QuerySkill):
    """List all database sessions."""

    name = "sessions"
    description = "显示所有数据库会话"
    query_name = "sessions_all"


@register_skill
class ActiveSessionsSkill(QuerySkill):
    """List active database sessions."""

    name = "activesessions"
    description = "显示活跃的数据库会话"
    aliases = ["active"]
    query_name = "sessions_active"