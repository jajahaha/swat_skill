"""Health check skill."""

from typing import List

from ..database.connection import ConnectionManager
from ..database.queries import get_query
from ..utils.formatter import Formatter, HealthItem
from .base import Skill, SkillResult, register_skill


@register_skill
class HealthSkill(Skill):
    """Full health check of PostgreSQL database."""

    name = "health"
    description = "全维度健康体检，检查连接、缓存、事务、死锁等指标"
    aliases = []

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute health check."""
        items = []
        overall_status = "ok"

        # Check connections
        result = conn.execute(get_query("health_connections"))
        if result.success and result.rows:
            row = result.rows[0]
            max_conn = int(row.get("max_connections", 100))
            curr_conn = int(row.get("current_connections", 0))
            conn_pct = float(row.get("connection_pct", 0))

            status = "ok"
            if conn_pct > 80:
                status = "warning"
                overall_status = "warning"
            elif conn_pct > 90:
                status = "critical"
                overall_status = "critical"

            items.append(HealthItem(
                category="基础",
                name="连接数",
                value=f"{curr_conn}/{max_conn} ({conn_pct:.1f}%)",
                status=status,
                tip="连接数过高" if status != "ok" else None,
            ))

        # Check cache hit ratio
        result = conn.execute(get_query("health_cache_hit"))
        if result.success and result.rows:
            row = result.rows[0]
            hit_ratio = float(row.get("cache_hit_ratio", 0))

            status = "ok"
            if hit_ratio < 95:
                status = "warning"
            elif hit_ratio < 90:
                status = "critical"

            items.append(HealthItem(
                category="性能",
                name="缓存命中率",
                value=f"{hit_ratio:.1f}%",
                status=status,
                tip="命中率低于95%，考虑增加shared_buffers" if status != "ok" else None,
            ))

        # Check deadlocks
        result = conn.execute(get_query("health_deadlocks"))
        if result.success and result.rows:
            row = result.rows[0]
            deadlocks = int(row.get("deadlocks", 0))

            status = "ok"
            if deadlocks > 0:
                status = "warning"
            elif deadlocks > 5:
                status = "critical"

            items.append(HealthItem(
                category="事务",
                name="死锁次数",
                value=str(deadlocks),
                status=status,
                tip=f"发现{deadlocks}次死锁，检查应用逻辑" if deadlocks > 0 else None,
            ))

        # Check transaction rollback ratio
        result = conn.execute(get_query("health_transactions"))
        if result.success and result.rows:
            row = result.rows[0]
            rollback_pct = float(row.get("rollback_pct", 0))

            status = "ok"
            if rollback_pct > 5:
                status = "warning"

            items.append(HealthItem(
                category="事务",
                name="事务回滚率",
                value=f"{rollback_pct:.1f}%",
                status=status,
            ))

        # Check temp files
        result = conn.execute(get_query("health_temp_files"))
        if result.success and result.rows:
            row = result.rows[0]
            temp_files = int(row.get("temp_files", 0))
            temp_bytes = row.get("temp_bytes", "0 bytes")

            status = "ok"
            if temp_files > 100:
                status = "warning"

            items.append(HealthItem(
                category="资源",
                name="临时文件",
                value=f"{temp_files} ({temp_bytes})",
                status=status,
                tip="临时文件过多，考虑增加work_mem" if status != "ok" else None,
            ))

        # Check active sessions
        result = conn.execute(get_query("sessions_active"))
        active_count = len(result.rows) if result.success else 0

        status = "ok"
        if active_count > 50:
            status = "warning"
        elif active_count > 100:
            status = "critical"

        items.append(HealthItem(
            category="会话",
            name="活跃会话",
            value=str(active_count),
            status=status,
        ))

        # Check long transactions
        result = conn.execute(get_query("long_transactions"))
        long_tx_count = len(result.rows) if result.success else 0

        status = "ok"
        if long_tx_count > 0:
            status = "warning"

        items.append(HealthItem(
            category="事务",
            name="长事务",
            value=str(long_tx_count),
            status=status,
            tip=f"发现{long_tx_count}个超过60秒的事务" if long_tx_count > 0 else None,
        ))

        # Check XID age
        result = conn.execute(get_query("xid_age"))
        if result.success and result.rows:
            row = result.rows[0]
            xid_age = int(row.get("xid_age", 0))
            percent_used = float(row.get("percent_used", 0))

            status = "ok"
            if percent_used > 50:
                status = "warning"
            elif percent_used > 80:
                status = "critical"

            items.append(HealthItem(
                category="维护",
                name="XID使用率",
                value=f"{percent_used:.1f}%",
                status=status,
                tip="XID接近wraparound，需要加强vacuum" if status != "ok" else None,
            ))

        return SkillResult(
            success=True,
            data={"items": items, "overall": overall_status},
            result_type="health",
        )