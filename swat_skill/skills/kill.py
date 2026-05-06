"""Kill session skill."""

from typing import List

from ..database.connection import ConnectionManager
from .base import Skill, SkillResult, register_skill
from ..utils.formatter import Formatter


@register_skill
class KillSkill(Skill):
    """Kill a database session."""

    name = "kill"
    description = "终止数据库会话"
    aliases = ["terminate"]

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute pg_terminate_backend."""
        if not args:
            return SkillResult(
                success=False,
                data=None,
                error="No PID provided. Usage: /kill <pid>",
            )

        pid = args[0]
        try:
            pid_int = int(pid)
        except ValueError:
            return SkillResult(
                success=False,
                data=None,
                error=f"Invalid PID: {pid}. Must be an integer.",
            )

        sql = f"SELECT pg_terminate_backend({pid_int}) as result"
        result = conn.execute(sql)

        if result.success and result.rows:
            success = result.rows[0].get("result", False)
            if success:
                return SkillResult(
                    success=True,
                    data=None,
                    message=f"Session {pid_int} terminated successfully",
                    result_type="text",
                )
            else:
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"Failed to terminate session {pid_int}",
                )

        return SkillResult(
            success=False,
            data=None,
            error=result.error or f"Failed to terminate session {pid_int}",
        )