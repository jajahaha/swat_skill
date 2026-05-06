"""Users skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import QuerySkill, register_skill


@register_skill
class UsersSkill(QuerySkill):
    """Show database users."""

    name = "users"
    description = "显示数据库用户"
    aliases = ["roles"]
    query_name = "users_all"