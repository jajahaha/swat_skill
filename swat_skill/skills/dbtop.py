"""Real-time performance panel skill (dbtop)."""

import time
from typing import List

from ..database.connection import ConnectionManager
from ..database.queries import get_query
from ..utils.formatter import Formatter
from .base import Skill, SkillResult, register_skill


@register_skill
class DbtopSkill(Skill):
    """Real-time performance panel similar to Linux top."""

    name = "dbtop"
    description = "实时性能面板，类似Linux top"
    aliases = ["top"]

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute dbtop - show real-time performance panel."""
        # Get refresh interval (default 1 second)
        interval = 1
        if args:
            try:
                interval = int(args[0])
            except ValueError:
                pass

        # Get iterations (default 5)
        iterations = 5
        if len(args) > 1:
            try:
                iterations = int(args[1])
            except ValueError:
                pass

        results = []
        for i in range(iterations):
            # Collect metrics
            metrics = self._collect_metrics(conn)
            results.append(metrics)

            if i < iterations - 1:
                time.sleep(interval)

        return SkillResult(
            success=True,
            data=results,
            result_type="dbtop",
        )

    def _collect_metrics(self, conn: ConnectionManager) -> dict:
        """Collect current performance metrics."""
        metrics = {}

        # Get active sessions
        result = conn.execute(get_query("sessions_active"))
        metrics["active_sessions"] = len(result.rows) if result.success else 0
        metrics["sessions_data"] = result.rows if result.success else []

        # Get wait events
        result = conn.execute(get_query("wait_events"))
        metrics["wait_events"] = result.rows if result.success else []

        # Get connection count
        result = conn.execute(get_query("health_connections"))
        if result.success and result.rows:
            row = result.rows[0]
            metrics["max_connections"] = int(row.get("max_connections", 0))
            metrics["current_connections"] = int(row.get("current_connections", 0))
        else:
            metrics["max_connections"] = 0
            metrics["current_connections"] = 0

        # Get buffer stats
        result = conn.execute(get_query("buffer_stats"))
        if result.success and result.rows:
            row = result.rows[0]
            metrics["cache_hit_ratio"] = float(row.get("cache_hit_ratio", 0))
        else:
            metrics["cache_hit_ratio"] = 0

        # Get transaction stats
        result = conn.execute(get_query("health_transactions"))
        if result.success and result.rows:
            row = result.rows[0]
            metrics["xact_commit"] = int(row.get("xact_commit", 0))
            metrics["xact_rollback"] = int(row.get("xact_rollback", 0))
        else:
            metrics["xact_commit"] = 0
            metrics["xact_rollback"] = 0

        # Timestamp
        metrics["timestamp"] = time.strftime("%H:%M:%S")

        return metrics