"""WebSocket handler for real-time command execution.

Manages WebSocket connections and command dispatch for web interface.
"""

import asyncio
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect

from ..config import Config, load_config
from ..database.queries import get_query
from ..skills.base import SkillRegistry
from ..skills.dbtop import DbStatsSnapshot, DbActivityRates
from .adapter import WebSession, create_web_session, WebFormatter


class SessionManager:
    """Manages active web sessions."""

    def __init__(self):
        self.sessions: Dict[str, WebSession] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_task(self) -> None:
        """Stop cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self) -> None:
        """Periodically cleanup expired sessions."""
        while True:
            await asyncio.sleep(60)  # Check every minute
            self.cleanup_expired()

    def cleanup_expired(self, max_age_minutes: int = 30) -> int:
        """Remove expired sessions."""
        expired = []
        for session_id, session in self.sessions.items():
            if session.is_expired(max_age_minutes):
                expired.append(session_id)

        for session_id in expired:
            session = self.sessions.pop(session_id, None)
            if session:
                session.disconnect()

        return len(expired)

    def create_session(self, config: Config) -> WebSession:
        """Create new session."""
        session = create_web_session(config)
        self.sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[WebSession]:
        return self.sessions.get(session_id)

    def remove_session(self, session_id: str) -> None:
        """Remove session."""
        session = self.sessions.pop(session_id, None)
        if session:
            session.disconnect()

    def get_active_count(self) -> int:
        """Get number of active sessions."""
        return len(self.sessions)


# Global session manager
session_manager = SessionManager()


async def handle_websocket(websocket: WebSocket, session_id: Optional[str] = None):
    """Handle WebSocket connection.

    Args:
        websocket: WebSocket connection.
        session_id: Optional existing session ID.
    """
    await websocket.accept()

    # Load config
    config = load_config()

    session = None

    try:
        # Create or get session
        if session_id:
            session = session_manager.get_session(session_id)
            if not session:
                # Create new session if ID not found
                session = session_manager.create_session(config)
        else:
            session = session_manager.create_session(config)

        # Send session info
        server_info = session.get_server_info()
        skill_names = [f"/{s.name}" for s in SkillRegistry.list()]
        # Database connection info for sidebar
        db_config = {
            "host": config.database.host,
            "port": config.database.port,
            "database": config.database.database,
            "user": config.database.user,
        }
        await websocket.send_json({
            "type": "connected",
            "session_id": session.id,
            "server_info": server_info,
            "skill_names": skill_names,
            "db_config": db_config,
        })

        while True:
            try:
                # Receive command from client
                data = await websocket.receive_json()
                command = data.get("command", "")

                if not command.strip():
                    continue

                # Check for exit command
                if command.strip().lower() in ("/exit", "/quit"):
                    await websocket.send_json({
                        "type": "exit",
                        "message": "Goodbye!",
                    })
                    break

                # Check if it's a dbtop command - handle with streaming
                cmd_lower = command.strip().lower()
                if cmd_lower.startswith("/dbtop") or cmd_lower.startswith("/top"):
                    await handle_dbtop_streaming(websocket, session, command)
                    continue

                # Dispatch command (wrap in try to catch execution errors)
                try:
                    result = session.dispatch(command)
                except Exception as e:
                    result = {"type": "error", "message": f"Execution error: {str(e)}"}

                # Send result
                await websocket.send_json(result)

                # Check if result indicates exit
                if result.get("type") == "exit":
                    break

            except json.JSONDecodeError:
                # Invalid JSON from client - send error but continue
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format",
                })
                continue

            except WebSocketDisconnect:
                # Client disconnected - exit loop
                break

    except WebSocketDisconnect:
        # Client disconnected during setup
        pass

    except Exception as e:
        # Setup error (database connection, etc.)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Session error: {str(e)}",
            })
        except Exception:
            pass  # WebSocket may already be closed

    finally:
        # Cleanup session on disconnect
        if session:
            session_manager.remove_session(session.id)


async def handle_dbtop_streaming(websocket: WebSocket, session: WebSession, command: str):
    """Handle dbtop command with real-time streaming updates.

    Sends dbtop updates in real-time instead of waiting for all iterations.

    Args:
        websocket: WebSocket connection.
        session: Web session with database connection.
        command: The dbtop command with optional parameters.
    """
    # Parse command parameters: /dbtop [interval] [iterations]
    parts = command.strip().split()
    interval = 2  # Default interval
    iterations = 10  # Default iterations

    if len(parts) > 1:
        try:
            interval = int(parts[1])
            if interval < 1:
                interval = 1
        except ValueError:
            pass

    if len(parts) > 2:
        try:
            iterations = int(parts[2])
        except ValueError:
            pass

    formatter = WebFormatter()

    # Track previous snapshot for rate calculation
    last_snapshot = None
    last_time = 0.0

    try:
        # Send initial message that dbtop is starting
        await websocket.send_json({
            "type": "dbtop_start",
            "message": f"开始 dbtop 监控 (间隔: {interval}s, 迭代: {iterations}次)",
            "interval": interval,
            "iterations": iterations,
        })

        for iteration in range(iterations):
            # Collect metrics
            metrics = await collect_dbtop_metrics(session.conn, last_snapshot, last_time)

            # Update snapshot for next iteration
            if 'snapshot' in metrics:
                last_snapshot = metrics['snapshot']
                last_time = metrics['timestamp']

            # Format for web display
            formatted = format_dbtop_for_web(metrics)

            # Send streaming update
            await websocket.send_json({
                "type": "dbtop_update",
                "iteration": iteration + 1,
                "total_iterations": iterations,
                "data": formatted,
            })

            # Wait for next iteration (except last)
            if iteration < iterations - 1:
                await asyncio.sleep(interval)

        # Send completion message
        await websocket.send_json({
            "type": "dbtop_end",
            "message": "dbtop 监控结束",
        })

    except WebSocketDisconnect:
        # Client disconnected during streaming
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"dbtop error: {str(e)}",
        })


async def collect_dbtop_metrics(conn, last_snapshot, last_time):
    """Collect dbtop metrics for streaming."""
    import time

    current_time = time.time()
    metrics = {}

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

    # Get cumulative database stats
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

    # Calculate rates
    rates = calculate_rates_from_snapshots(current_snapshot, last_snapshot, last_time)
    metrics['rates'] = rates
    metrics['snapshot'] = current_snapshot
    metrics['timestamp'] = current_time

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

    # Timestamp string
    metrics['timestamp_str'] = time.strftime("%H:%M:%S")

    return metrics


def calculate_rates_from_snapshots(current, last, last_time):
    """Calculate per-second rates from snapshot deltas."""
    rates = DbActivityRates()

    if last is None:
        # First iteration - no rates yet
        total_blocks = current.blks_read + current.blks_hit
        if total_blocks > 0:
            rates.buffer_hit_pct = 100.0 * current.blks_hit / total_blocks
        return rates

    time_diff = current.timestamp - last_time
    if time_diff <= 0:
        return rates

    delta_commit = current.xact_commit - last.xact_commit
    delta_rollback = current.xact_rollback - last.xact_rollback
    delta_blks_read = current.blks_read - last.blks_read
    delta_blks_hit = current.blks_hit - last.blks_hit
    delta_tup_fetched = current.tup_fetched - last.tup_fetched
    delta_tup_inserted = current.tup_inserted - last.tup_inserted
    delta_tup_updated = current.tup_updated - last.tup_updated
    delta_tup_deleted = current.tup_deleted - last.tup_deleted

    rates.tps = delta_commit / time_diff
    rates.rollbacks_ps = delta_rollback / time_diff
    rates.buffer_reads_ps = delta_blks_read / time_diff

    total_block_delta = delta_blks_read + delta_blks_hit
    if total_block_delta > 0:
        rates.buffer_hit_pct = 100.0 * delta_blks_hit / total_block_delta
    else:
        total_blocks = current.blks_read + current.blks_hit
        if total_blocks > 0:
            rates.buffer_hit_pct = 100.0 * current.blks_hit / total_blocks

    rates.row_reads_ps = delta_tup_fetched / time_diff
    rates.row_writes_ps = (delta_tup_inserted + delta_tup_updated + delta_tup_deleted) / time_diff

    return rates


def format_dbtop_for_web(metrics):
    """Format dbtop metrics for web display."""
    rates = metrics.get('rates', DbActivityRates())
    states = metrics.get('session_states', {})

    formatted = {
        "timestamp": metrics.get("timestamp_str", ""),
        "uptime": metrics.get("uptime", ""),
        # DB activity rates (pg_top style)
        "db_activity": {
            "tps": round(rates.tps, 2),
            "rollbacks_ps": round(rates.rollbacks_ps, 2),
            "buffer_reads_ps": round(rates.buffer_reads_ps, 2),
            "buffer_hit_pct": round(rates.buffer_hit_pct, 1),
            "row_reads_ps": round(rates.row_reads_ps, 1),
            "row_writes_ps": round(rates.row_writes_ps, 1),
        },
        # Session states breakdown
        "session_states": {
            "total": states.get('total', 0),
            "active": states.get('active', 0),
            "idle": states.get('idle', 0),
            "idle_tx": states.get('idle_in_transaction', 0),
        },
    }

    # Format sessions for table display
    if metrics.get("sessions_data"):
        sessions_table = []
        for session in metrics["sessions_data"]:
            duration = session.get("duration_seconds")
            dur_str = format_duration_plain(duration)
            xact_dur = session.get("xact_duration_seconds")
            xact_str = format_duration_plain(xact_dur)

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
        formatted["sessions"] = sessions_table

    # Format wait events
    if metrics.get("wait_events"):
        wait_table = []
        for event in metrics["wait_events"][:5]:
            wait_table.append({
                "Type": event.get("wait_event_type", ""),
                "Event": event.get("wait_event", ""),
                "Count": event.get("count", 0),
            })
        formatted["wait_events"] = wait_table

    return formatted


def format_duration_plain(duration):
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


async def handle_command_http(session_id: str, command: str) -> Dict:
    """Handle command via HTTP API.

    Args:
        session_id: Session ID.
        command: Command to execute.

    Returns:
        JSON result.
    """
    session = session_manager.get_session(session_id)
    if not session:
        return {"type": "error", "message": "Session not found"}

    return session.dispatch(command)