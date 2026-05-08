"""Real-time performance panel skill (dbtop).

Implements a PostgreSQL monitoring display similar to pg_top, featuring:
- Database activity metrics (tps, rollbacks/s, buffer reads/s, hit%, row r/s, row w/s)
- Session state breakdown
- Real-time session table with wait events
- Rate calculations based on cumulative stat differences
"""

import time
from typing import List, Optional
from dataclasses import dataclass, field

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


@dataclass
class DbStatsSnapshot:
    """Snapshot of cumulative database statistics for rate calculation."""
    xact_commit: int = 0
    xact_rollback: int = 0
    blks_read: int = 0
    blks_hit: int = 0
    tup_fetched: int = 0
    tup_inserted: int = 0
    tup_updated: int = 0
    tup_deleted: int = 0
    conflicts: int = 0
    deadlocks: int = 0
    timestamp: float = 0.0


@dataclass
class DbActivityRates:
    """Per-second rate metrics calculated from stat deltas."""
    tps: float = 0.0          # transactions per second (commits)
    rollbacks_ps: float = 0.0  # rollbacks per second
    buffer_reads_ps: float = 0.0  # buffer reads per second
    buffer_hit_pct: float = 0.0   # buffer hit percentage (instant)
    row_reads_ps: float = 0.0     # rows fetched per second
    row_writes_ps: float = 0.0    # rows inserted+updated+deleted per second
    deadlocks_ps: float = 0.0     # deadlocks per second


@register_skill
class DbtopSkill(Skill):
    """Real-time performance panel similar to pg_top."""

    name = "dbtop"
    description = "实时性能面板，类似pg_top"
    aliases = ["top"]
    params = ["[interval] [iterations]"]

    # Store previous snapshot for rate calculation
    _last_snapshot: Optional[DbStatsSnapshot] = None
    _last_time: float = 0.0

    def execute(
        self,
        conn: ConnectionManager,
        args: List[str],
        formatter: Formatter,
    ) -> SkillResult:
        """Execute dbtop - show real-time performance panel."""
        # Get refresh interval (default 2 seconds for better rate calculation)
        interval = 2
        if args:
            try:
                interval = int(args[0])
                if interval < 1:
                    interval = 1
            except ValueError:
                pass

        # Get iterations (default 10, 0 means infinite)
        iterations = 10
        if len(args) > 1:
            try:
                iterations = int(args[1])
            except ValueError:
                pass

        # Reset snapshot on new execution
        self._last_snapshot = None
        self._last_time = 0.0

        # Check if we're in CLI mode (has console) or Web mode
        is_cli = hasattr(formatter, 'console') and formatter.console is not None

        if is_cli:
            return self._execute_cli(conn, formatter, interval, iterations)
        else:
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
                metrics = self._collect_all_metrics(conn)
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
        """Format dbtop display using Rich Layout - pg_top style."""
        layout = Layout()
        layout.split(
            Layout(name="header", size=2),
            Layout(name="db_activity", size=2),  # pg_top style DB activity row
            Layout(name="process_states", size=1),  # session state breakdown
            Layout(name="table", ratio=1),
            Layout(name="footer", size=1),
        )

        # Header - title and time (pg_top style)
        header_text = Text()
        header_text.append("SWAT SKILL dbtop", style="bold cyan")
        header_text.append(" - PostgreSQL Monitor", style="dim")

        # Add uptime if available
        uptime = metrics.get('uptime', '')
        if uptime:
            header_text.append(f"  Up: {uptime}", style="green")

        header_text.append(f"  {metrics['timestamp']}", style="white")
        layout["header"].update(Panel(header_text, box=box.SIMPLE, style="cyan"))

        # DB Activity row - pg_top style: "tps, rollbs/s, buffer r/s, hit%, row r/s, row w/s"
        rates = metrics.get('rates', DbActivityRates())
        db_text = Text()
        db_text.append("DB activity: ", style="bold yellow")
        db_text.append(f"{rates.tps:.1f} tps, ", style="green")
        db_text.append(f"{rates.rollbacks_ps:.1f} rollbs/s, ", style="default")
        db_text.append(f"{rates.buffer_reads_ps:.1f} buffer r/s, ", style="default")

        # Buffer hit percentage with color
        if rates.buffer_hit_pct >= 90:
            db_text.append(f"{rates.buffer_hit_pct:.0f}% hit", style="green")
        elif rates.buffer_hit_pct >= 70:
            db_text.append(f"{rates.buffer_hit_pct:.0f}% hit", style="yellow")
        else:
            db_text.append(f"{rates.buffer_hit_pct:.0f}% hit", style="red")

        db_text.append(f", {rates.row_reads_ps:.0f} row r/s, ", style="default")
        db_text.append(f"{rates.row_writes_ps:.0f} row w/s", style="default")

        layout["db_activity"].update(Panel(db_text, box=box.SIMPLE))

        # Process states - pg_top style breakdown
        states = metrics.get('session_states', {})
        state_text = Text()
        state_text.append("Sessions: ", style="bold")
        total = states.get('total', 0)
        active = states.get('active', 0)
        idle = states.get('idle', 0)
        idle_tx = states.get('idle_in_transaction', 0)

        state_text.append(f"{total} total: ", style="default")
        state_text.append(f"{active} active", style="green bold" if active > 0 else "dim")
        state_text.append(f", {idle} idle", style="dim")
        if idle_tx > 0:
            state_text.append(f", {idle_tx} idle_tx", style="yellow bold")

        layout["process_states"].update(Panel(state_text, box=box.SIMPLE))

        # Table - session list (pg_top style columns)
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.SIMPLE_HEAD,
            expand=True,
        )
        table.add_column("PID", style="cyan", width=7)
        table.add_column("USER", width=10)
        table.add_column("STATE", width=10)
        table.add_column("DURATION", width=8)
        table.add_column("XACT", width=7)
        table.add_column("WAIT", width=12)
        table.add_column("QUERY", ratio=1)

        sessions_data = metrics.get('sessions_data', [])
        if sessions_data:
            for session in sessions_data:
                pid = str(session.get('pid', ''))
                user = str(session.get('usename', ''))[:10]

                # State with color
                state = str(session.get('state', ''))
                state_display = self._format_state(state)

                # Query duration
                query_dur = session.get('duration_seconds')
                dur_display = self._format_duration(query_dur)

                # Transaction duration (if available)
                xact_dur = session.get('xact_duration_seconds')
                xact_display = self._format_duration(xact_dur, short=True)

                # Wait event
                wait_type = session.get('wait_event_type', '')
                wait_event = session.get('wait_event', '')
                wait_display = self._format_wait_event(wait_type, wait_event)

                # Query preview
                query = str(session.get('query_preview', '') or '').strip()
                if len(query) > 60:
                    query = query[:57] + "..."

                table.add_row(pid, user, state_display, dur_display, xact_display, wait_display, query)
        else:
            table.add_row("-", "-", "[dim]no sessions[/dim]", "-", "-", "-", "-")

        layout["table"].update(table)

        # Footer - wait events summary
        footer_text = Text()
        footer_text.append("Wait Events: ", style="bold yellow")
        wait_events = metrics.get('wait_events', [])
        if wait_events:
            event_strs = []
            for event in wait_events[:5]:
                event_name = event.get('wait_event', '')
                count = event.get('count', 0)
                if event_name:
                    event_strs.append(f"{event_name}({count})")
            footer_text.append(", ".join(event_strs), style="default")
        else:
            footer_text.append("none", style="dim")

        layout["footer"].update(Panel(footer_text, box=box.SIMPLE, style="yellow"))

        return layout

    def _format_state(self, state: str) -> str:
        """Format session state with color."""
        if state == 'active':
            return "[green]active[/green]"
        elif state == 'idle':
            return "[dim]idle[/dim]"
        elif state == 'idle in transaction':
            return "[yellow]idle_tx[/yellow]"
        elif state == 'idle in transaction aborted':
            return "[red]abort[/red]"
        elif state == 'fastpath function call':
            return "[blue]fast[/blue]"
        elif state == 'disabled':
            return "[red]disabl[/red]"
        else:
            return state[:10]

    def _format_duration(self, duration: Optional[float], short: bool = False) -> str:
        """Format duration with color based on length."""
        if duration is None or duration < 0:
            return "-"

        dur_val = float(duration)
        if dur_val < 1:
            dur_str = f"{dur_val:.2f}s"
        elif dur_val < 60:
            dur_str = f"{dur_val:.1f}s"
        elif dur_val < 3600:
            dur_str = f"{dur_val/60:.1f}m"
        else:
            dur_str = f"{dur_val/3600:.1f}h"

        # Color by duration
        if dur_val > 300:  # > 5 minutes
            return f"[red]{dur_str}[/red]"
        elif dur_val > 60:  # > 1 minute
            return f"[yellow]{dur_str}[/yellow]"
        elif dur_val > 10:  # > 10 seconds
            return f"[cyan]{dur_str}[/cyan]"
        else:
            return dur_str

    def _format_wait_event(self, wait_type: str, wait_event: str) -> str:
        """Format wait event display."""
        if not wait_type or not wait_event:
            return "-"

        # Shorten common wait event types
        type_short = wait_type[:4] if wait_type else ""
        event_short = wait_event[:8] if wait_event else ""
        return f"{type_short}:{event_short}"

    def _execute_web(
        self,
        conn: ConnectionManager,
        interval: int,
        iterations: int,
    ) -> SkillResult:
        """Execute in Web mode, return formatted data."""
        results = []
        for i in range(iterations):
            metrics = self._collect_all_metrics(conn)
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
        rates = metrics.get('rates', DbActivityRates())
        states = metrics.get('session_states', {})

        formatted = {
            "timestamp": metrics.get("timestamp", ""),
            "uptime": metrics.get("uptime", ""),
            # DB activity rates
            "tps": round(rates.tps, 2),
            "rollbacks_ps": round(rates.rollbacks_ps, 2),
            "buffer_reads_ps": round(rates.buffer_reads_ps, 2),
            "buffer_hit_pct": round(rates.buffer_hit_pct, 1),
            "row_reads_ps": round(rates.row_reads_ps, 1),
            "row_writes_ps": round(rates.row_writes_ps, 1),
            # Session states
            "sessions_total": states.get('total', 0),
            "sessions_active": states.get('active', 0),
            "sessions_idle": states.get('idle', 0),
            "sessions_idle_tx": states.get('idle_in_transaction', 0),
        }

        # Format sessions for table display
        if metrics.get("sessions_data"):
            sessions_table = []
            for session in metrics["sessions_data"]:
                duration = session.get("duration_seconds")
                dur_str = self._format_duration_plain(duration)
                xact_dur = session.get("xact_duration_seconds")
                xact_str = self._format_duration_plain(xact_dur)

                wait_type = session.get("wait_event_type", "")
                wait_event = session.get("wait_event", "")
                wait_str = f"{wait_type}:{wait_event}" if wait_type and wait_event else "-"

                query = str(session.get("query_preview", "") or "").strip()
                if len(query) > 100:
                    query = query[:97] + "..."

                sessions_table.append({
                    "PID": session.get("pid", ""),
                    "User": session.get("usename", ""),
                    "State": session.get("state", ""),
                    "Duration": dur_str,
                    "Xact": xact_str,
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

    def _format_duration_plain(self, duration: Optional[float]) -> str:
        """Format duration without Rich markup."""
        if duration is None or duration < 0:
            return "-"

        dur_val = float(duration)
        if dur_val < 1:
            return f"{dur_val:.2f}s"
        elif dur_val < 60:
            return f"{dur_val:.1f}s"
        elif dur_val < 3600:
            return f"{dur_val/60:.1f}m"
        else:
            return f"{dur_val/3600:.1f}h"

    def _collect_all_metrics(self, conn: ConnectionManager) -> dict:
        """Collect all metrics including rate calculations."""
        metrics = {}
        current_time = time.time()

        # Get server uptime
        result = conn.execute(get_query("uptime"))
        if result.success and result.rows:
            uptime_sec = float(result.rows[0].get('uptime_seconds', 0))
            if uptime_sec < 60:
                metrics['uptime'] = f"{uptime_sec:.0f}s"
            elif uptime_sec < 3600:
                metrics['uptime'] = f"{uptime_sec/60:.0f}m"
            elif uptime_sec < 86400:
                metrics['uptime'] = f"{uptime_sec/3600:.1f}h"
            else:
                days = int(uptime_sec / 86400)
                hours = int((uptime_sec % 86400) / 3600)
                metrics['uptime'] = f"{days}d {hours}h"

        # Get cumulative database stats for rate calculation
        result = conn.execute(get_query("db_stats_cumulative"))
        current_snapshot = DbStatsSnapshot(timestamp=current_time)
        if result.success and result.rows:
            row = result.rows[0]
            current_snapshot.xact_commit = int(row.get('xact_commit', 0) or 0)
            current_snapshot.xact_rollback = int(row.get('xact_rollback', 0) or 0)
            current_snapshot.blks_read = int(row.get('blks_read', 0) or 0)
            current_snapshot.blks_hit = int(row.get('blks_hit', 0) or 0)
            current_snapshot.tup_fetched = int(row.get('tup_fetched', 0) or 0)
            current_snapshot.tup_inserted = int(row.get('tup_inserted', 0) or 0)
            current_snapshot.tup_updated = int(row.get('tup_updated', 0) or 0)
            current_snapshot.tup_deleted = int(row.get('tup_deleted', 0) or 0)
            current_snapshot.conflicts = int(row.get('conflicts', 0) or 0)
            current_snapshot.deadlocks = int(row.get('deadlocks', 0) or 0)

        # Calculate rates from delta
        rates = self._calculate_rates(current_snapshot)
        metrics['rates'] = rates

        # Store snapshot for next iteration
        self._last_snapshot = current_snapshot
        self._last_time = current_time

        # Get session state counts
        result = conn.execute(get_query("session_state_counts"))
        if result.success and result.rows:
            metrics['session_states'] = result.rows[0]
        else:
            metrics['session_states'] = {}

        # Get sessions with details
        result = conn.execute(get_query("sessions_with_state"))
        metrics['sessions_data'] = result.rows if result.success else []

        # Get wait events
        result = conn.execute(get_query("wait_events"))
        metrics['wait_events'] = result.rows if result.success else []

        # Timestamp
        metrics['timestamp'] = time.strftime("%H:%M:%S")

        return metrics

    def _calculate_rates(self, current: DbStatsSnapshot) -> DbActivityRates:
        """Calculate per-second rates from cumulative stat deltas.

        This mimics pg_top's get_database_info() function which computes
        (current - last) / time_diff to get per-second rates.
        """
        rates = DbActivityRates()

        if self._last_snapshot is None:
            # First iteration - no rates yet, but calculate instant hit%
            total_blocks = current.blks_read + current.blks_hit
            if total_blocks > 0:
                rates.buffer_hit_pct = 100.0 * current.blks_hit / total_blocks
            return rates

        # Calculate time difference
        time_diff = current.timestamp - self._last_time
        if time_diff <= 0:
            return rates

        # Calculate deltas and rates
        delta_commit = current.xact_commit - self._last_snapshot.xact_commit
        delta_rollback = current.xact_rollback - self._last_snapshot.xact_rollback
        delta_blks_read = current.blks_read - self._last_snapshot.blks_read
        delta_blks_hit = current.blks_hit - self._last_snapshot.blks_hit
        delta_tup_fetched = current.tup_fetched - self._last_snapshot.tup_fetched
        delta_tup_inserted = current.tup_inserted - self._last_snapshot.tup_inserted
        delta_tup_updated = current.tup_updated - self._last_snapshot.tup_updated
        delta_tup_deleted = current.tup_deleted - self._last_snapshot.tup_deleted
        delta_deadlocks = current.deadlocks - self._last_snapshot.deadlocks

        # Per-second rates
        rates.tps = delta_commit / time_diff
        rates.rollbacks_ps = delta_rollback / time_diff
        rates.buffer_reads_ps = delta_blks_read / time_diff

        # Buffer hit percentage (instant, based on delta)
        total_block_delta = delta_blks_read + delta_blks_hit
        if total_block_delta > 0:
            rates.buffer_hit_pct = 100.0 * delta_blks_hit / total_block_delta
        else:
            # Use cumulative if no delta
            total_blocks = current.blks_read + current.blks_hit
            if total_blocks > 0:
                rates.buffer_hit_pct = 100.0 * current.blks_hit / total_blocks

        # Row stats
        rates.row_reads_ps = delta_tup_fetched / time_diff
        rates.row_writes_ps = (delta_tup_inserted + delta_tup_updated + delta_tup_deleted) / time_diff
        rates.deadlocks_ps = delta_deadlocks / time_diff

        return rates