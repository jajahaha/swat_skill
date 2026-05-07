"""Real-time performance panel skill (dbtop)."""

import time
from typing import List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box

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
            # CLI mode: use Layout for real-time display
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
        """Execute in CLI mode with real-time display using Layout."""
        console = formatter.console

        try:
            iteration = 0
            while iterations == 0 or iteration < iterations:
                metrics = self._collect_metrics(conn)
                layout = self._format_dbtop_layout(metrics)
                console.clear()
                console.print(layout)

                if iterations != 0 and iteration < iterations - 1:
                    time.sleep(interval)
                iteration += 1

        except KeyboardInterrupt:
            console.print("\n[yellow]dbtop stopped[/yellow]")

        return SkillResult(success=True, data=None, result_type="text", message="dbtop completed")

    def _format_dbtop_layout(self, metrics: dict) -> Layout:
        """Format dbtop display using Rich Layout - similar to pg_top style."""
        # Create main layout
        layout = Layout()
        layout.split(
            Layout(name="header", size=2),
            Layout(name="stats", size=2),
            Layout(name="table", ratio=1),
            Layout(name="footer", size=1),
        )

        # Header - title and time
        header_text = Text()
        header_text.append("SWAT SKILL dbtop", style="bold cyan")
        header_text.append(" - PostgreSQL Monitor", style="dim")
        header_text.append(f"          {metrics['timestamp']}", style="white")
        layout["header"].update(Panel(header_text, box=box.SIMPLE, style="cyan"))

        # Stats - summary line
        sessions = metrics.get('active_sessions', 0)
        total_conn = metrics.get('current_connections', 0)
        max_conn = metrics.get('max_connections', 0)
        cache_hit = metrics.get('cache_hit_ratio', 0)
        xact_commit = metrics.get('xact_commit', 0)
        xact_rollback = metrics.get('xact_rollback', 0)

        # Calculate TPS (approximate)
        tps = xact_commit  # This is cumulative, not per-second

        stats_text = Text()
        stats_text.append(f"Active: ", style="dim")
        stats_text.append(f"{sessions}", style="green bold")
        stats_text.append(f"   Total: {total_conn}/{max_conn}", style="default")
        stats_text.append(f"   Cache: ", style="dim")
        if cache_hit >= 90:
            stats_text.append(f"{cache_hit:.1f}%", style="green")
        elif cache_hit >= 70:
            stats_text.append(f"{cache_hit:.1f}%", style="yellow")
        else:
            stats_text.append(f"{cache_hit:.1f}%", style="red")
        stats_text.append(f"   Commit: {xact_commit}", style="default")
        stats_text.append(f"   Rollback: {xact_rollback}", style="default")
        layout["stats"].update(Panel(stats_text, box=box.SIMPLE))

        # Table - session list
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.SIMPLE_HEAD,
            expand=True,
        )
        table.add_column("PID", style="cyan", width=8)
        table.add_column("USER", width=12)
        table.add_column("STATE", width=12)
        table.add_column("DURATION", width=10)
        table.add_column("WAIT", width=14)
        table.add_column("QUERY", width=40)

        sessions_data = metrics.get('sessions_data', [])
        if sessions_data:
            for session in sessions_data:
                pid = str(session.get('pid', ''))

                # User (truncate if needed)
                user = str(session.get('usename', ''))[:12]

                # State with color
                state = str(session.get('state', ''))
                if state == 'active':
                    state_display = f"[green]active[/green]"
                elif state == 'idle':
                    state_display = f"[dim]idle[/dim]"
                elif state == 'idle in transaction':
                    state_display = f"[yellow]idle_tx[/yellow]"
                else:
                    state_display = state[:12]

                # Duration
                duration = session.get('duration_seconds')
                if duration is not None and float(duration) >= 0:
                    dur_val = float(duration)
                    if dur_val < 1:
                        dur_str = f"{dur_val:.2f}s"
                    elif dur_val < 60:
                        dur_str = f"{dur_val:.1f}s"
                    else:
                        dur_str = f"{dur_val/60:.1f}m"
                    # Color by duration
                    if dur_val > 60:
                        dur_display = f"[red]{dur_str}[/red]"
                    elif dur_val > 10:
                        dur_display = f"[yellow]{dur_str}[/yellow]"
                    else:
                        dur_display = dur_str
                else:
                    dur_display = "-"

                # Wait event
                wait_type = session.get('wait_event_type', '')
                wait_event = session.get('wait_event', '')
                if wait_type and wait_event:
                    wait_display = f"{wait_type[:6]}:{wait_event[:8]}"
                else:
                    wait_display = "-"

                # Query preview
                query = str(session.get('query_preview', '') or '')
                # Clean up query - remove leading whitespace
                query = query.strip()
                if len(query) > 40:
                    query = query[:37] + "..."

                table.add_row(pid, user, state_display, dur_display, wait_display, query)
        else:
            # No active sessions
            table.add_row("-", "-", "[dim]no active[/dim]", "-", "-", "-")

        layout["table"].update(table)

        # Footer - wait events summary
        footer_text = Text()
        footer_text.append("Wait Events: ", style="bold yellow")
        wait_events = metrics.get('wait_events', [])
        if wait_events:
            event_strs = []
            for event in wait_events[:5]:
                event_type = event.get('wait_event_type', '')
                event_name = event.get('wait_event', '')
                count = event.get('count', 0)
                if event_type and event_name:
                    event_strs.append(f"{event_name}({count})")
            footer_text.append(", ".join(event_strs), style="default")
        else:
            footer_text.append("none", style="dim")

        layout["footer"].update(Panel(footer_text, box=box.SIMPLE, style="yellow"))

        return layout

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
                # Format duration
                duration = session.get("duration_seconds")
                if duration is not None and float(duration) >= 0:
                    dur_val = float(duration)
                    if dur_val < 1:
                        dur_str = f"{dur_val:.2f}s"
                    elif dur_val < 60:
                        dur_str = f"{dur_val:.1f}s"
                    else:
                        dur_str = f"{dur_val/60:.1f}m"
                else:
                    dur_str = "-"

                # Format wait event
                wait_type = session.get("wait_event_type", "")
                wait_event = session.get("wait_event", "")
                if wait_type and wait_event:
                    wait_str = f"{wait_type}:{wait_event}"
                else:
                    wait_str = "-"

                # Query preview
                query = str(session.get("query_preview", "") or "").strip()
                if len(query) > 50:
                    query = query[:47] + "..."

                sessions_table.append({
                    "PID": session.get("pid", ""),
                    "User": session.get("usename", ""),
                    "State": session.get("state", ""),
                    "Duration": dur_str,
                    "Wait": wait_str,
                    "Query": query,
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

        # Get all sessions count
        result = conn.execute(get_query("sessions_all"))
        metrics["total_sessions"] = len(result.rows) if result.success else 0

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