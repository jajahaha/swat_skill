"""Real-time performance panel skill (dbtop)."""

import time
from typing import List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

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
    params = ["[interval] [iterations]"]

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

        # Get iterations (default 5, 0 means infinite)
        iterations = 5
        if len(args) > 1:
            try:
                iterations = int(args[1])
            except ValueError:
                pass

        # Check if we're in CLI mode (has console) or Web mode
        is_cli = hasattr(formatter, 'console') and formatter.console is not None

        if is_cli:
            # CLI mode: use Live for real-time display
            return self._execute_cli(conn, formatter, interval, iterations)
        else:
            # Web mode: return formatted data
            return self._execute_web(conn, interval, iterations)

    def _execute_cli(
        self,
        conn: ConnectionManager,
        formatter: Formatter,
        interval: int,
        iterations: int,
    ) -> SkillResult:
        """Execute in CLI mode with real-time display."""
        console = formatter.console

        try:
            iteration = 0
            while iterations == 0 or iteration < iterations:
                metrics = self._collect_metrics(conn)
                panel = self._format_dbtop_panel(metrics, console)
                console.clear()
                console.print(panel)

                if iterations != 0 and iteration < iterations - 1:
                    time.sleep(interval)
                iteration += 1

        except KeyboardInterrupt:
            console.print("\n[yellow]dbtop stopped[/yellow]")

        return SkillResult(success=True, data=None, result_type="text", message="dbtop completed")

    def _execute_web(
        self,
        conn: ConnectionManager,
        interval: int,
        iterations: int,
    ) -> SkillResult:
        """Execute in Web mode, return formatted data."""
        results = []
        for i in range(iterations):
            metrics = self._collect_metrics(conn)
            # Format for web display
            formatted = self._format_for_web(metrics)
            results.append(formatted)

            if i < iterations - 1:
                time.sleep(interval)

        return SkillResult(
            success=True,
            data=results,
            result_type="dbtop",
        )

    def _format_dbtop_panel(self, metrics: dict, console: Console) -> Panel:
        """Format dbtop as a panel similar to Linux top."""
        lines = []

        # Header line
        lines.append(f"[bold cyan]SWAT SKILL dbtop[/bold cyan] - {metrics['timestamp']}")
        lines.append(f"[dim]Press Ctrl+C to stop[/dim]")
        lines.append("")

        # Summary line
        sessions = metrics.get('active_sessions', 0)
        max_conn = metrics.get('max_connections', 0)
        curr_conn = metrics.get('current_connections', 0)
        cache_hit = metrics.get('cache_hit_ratio', 0)

        lines.append(f"[bold]Summary:[/bold]")
        lines.append(f"  Active Sessions: [green]{sessions}[/green]")
        lines.append(f"  Connections: {curr_conn}/{max_conn}")
        lines.append(f"  Cache Hit Ratio: [green]{cache_hit:.1f}%[/green]")
        lines.append(f"  Transactions: commit={metrics.get('xact_commit', 0)}, rollback={metrics.get('xact_rollback', 0)}")
        lines.append("")

        # Active sessions table
        if metrics.get('sessions_data'):
            lines.append("[bold]Active Sessions:[/bold]")

            # Create table
            table = Table(show_header=True, header_style="bold cyan", box=None)
            table.add_column("PID", style="cyan", width=8)
            table.add_column("User", width=10)
            table.add_column("State", width=10)
            table.add_column("Duration", width=10)
            table.add_column("Query Preview", width=40)

            for session in metrics['sessions_data']:
                pid = str(session.get('pid', ''))
                user = session.get('usename', '')[:10]
                state = session.get('state', '')
                duration = session.get('duration_seconds', 0)

                # Format duration
                if duration >= 0:
                    dur_str = f"{float(duration):.2f}s"
                else:
                    dur_str = "N/A"

                # Query preview
                query = session.get('query_preview', '')
                if len(query) > 40:
                    query = query[:37] + "..."

                # Color state
                if state == 'active':
                    state_str = f"[green]{state}[/green]"
                elif state == 'idle':
                    state_str = f"[dim]{state}[/dim]"
                else:
                    state_str = state

                table.add_row(pid, user, state_str, dur_str, query)

            lines.append(table)
        else:
            lines.append("[dim]No active sessions[/dim]")

        lines.append("")

        # Wait events
        if metrics.get('wait_events'):
            lines.append("[bold yellow]Wait Events:[/bold yellow]")
            for event in metrics['wait_events'][:5]:
                event_type = event.get('wait_event_type', '')
                event_name = event.get('wait_event', '')
                count = event.get('count', 0)
                lines.append(f"  {event_type}: {event_name} ({count})")
        else:
            lines.append("[dim]No wait events[/dim]")

        return Panel("\n".join(str(line) for line in lines), border_style="cyan", title="Database Top")

    def _format_for_web(self, metrics: dict) -> dict:
        """Format metrics for web display."""
        # Simplify data for web
        formatted = {
            "timestamp": metrics.get("timestamp", ""),
            "active_sessions": metrics.get("active_sessions", 0),
            "current_connections": metrics.get("current_connections", 0),
            "max_connections": metrics.get("max_connections", 0),
            "cache_hit_ratio": round(metrics.get("cache_hit_ratio", 0), 2),
            "xact_commit": metrics.get("xact_commit", 0),
            "xact_rollback": metrics.get("xact_rollback", 0),
        }

        # Format sessions for table display
        if metrics.get("sessions_data"):
            sessions_table = []
            for session in metrics["sessions_data"]:
                sessions_table.append({
                    "PID": session.get("pid", ""),
                    "User": session.get("usename", ""),
                    "State": session.get("state", ""),
                    "Duration": str(session.get("duration_seconds", "")),
                    "Query Preview": (session.get("query_preview", "") or "")[:50],
                })
            formatted["sessions_table"] = sessions_table

        # Format wait events
        if metrics.get("wait_events"):
            wait_table = []
            for event in metrics["wait_events"][:5]:
                wait_table.append({
                    "Type": event.get("wait_event_type", ""),
                    "Event": event.get("wait_event", ""),
                    "Count": event.get("count", 0),
                })
            formatted["wait_events_table"] = wait_table

        return formatted

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