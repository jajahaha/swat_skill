"""Web adapter for converting CLI output to JSON format.

Adapts the CLI Dispatcher and Formatter to web-friendly JSON output.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..config import Config
from ..database.connection import ConnectionManager, create_connection_manager
from ..dispatcher.router import Dispatcher
from ..skills.base import SkillResult
from ..utils.formatter import HealthItem


class WebFormatter:
    """Formatter for web output (JSON-based)."""

    def format_table(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        execution_time: float = 0.0,
    ) -> Dict:
        """Format table data as JSON."""
        if not data:
            return {
                "type": "table",
                "columns": columns or [],
                "rows": [],
                "row_count": 0,
                "execution_time": execution_time,
            }

        if columns is None:
            columns = list(data[0].keys())

        return {
            "type": "table",
            "columns": columns,
            "rows": data,
            "row_count": len(data),
            "execution_time": execution_time,
        }

    def format_health_report(
        self,
        items: List[HealthItem],
        overall_status: str = "ok",
        title: str = "Database Health",
    ) -> Dict:
        """Format health report as JSON."""
        return {
            "type": "health",
            "title": title,
            "overall": overall_status,
            "items": [
                {
                    "category": item.category,
                    "name": item.name,
                    "value": item.value,
                    "status": item.status,
                    "tip": item.tip,
                }
                for item in items
            ],
        }

    def format_error(self, error: str) -> Dict:
        """Format error message as JSON."""
        return {"type": "error", "message": error}

    def format_success(self, message: str) -> Dict:
        """Format success message as JSON."""
        return {"type": "success", "message": message}

    def format_info(self, message: str) -> Dict:
        """Format info message as JSON."""
        return {"type": "info", "message": message}

    def format_text(self, content: str) -> Dict:
        """Format plain text as JSON."""
        return {"type": "text", "content": content}

    def format_empty(self) -> Dict:
        """Format empty result."""
        return {"type": "empty"}

    def format_exit(self, message: str = "Goodbye!") -> Dict:
        """Format exit result."""
        return {"type": "exit", "message": message}

    def format_llm_step(self, step_type: str, content: str) -> Dict:
        """Format LLM intermediate step."""
        return {
            "type": "llm_step",
            "step": step_type,
            "content": content,
        }

    def format_dbtop(self, data: List[Dict]) -> Dict:
        """Format dbtop results for web display - pg_top style."""
        if not data:
            return {"type": "info", "message": "No data collected"}

        # Return the latest snapshot as summary
        latest = data[-1]

        return {
            "type": "dbtop",
            "timestamp": latest.get("timestamp", ""),
            "uptime": latest.get("uptime", ""),
            # DB activity rates (pg_top style)
            "db_activity": {
                "tps": latest.get("tps", 0),
                "rollbacks_ps": latest.get("rollbacks_ps", 0),
                "buffer_reads_ps": latest.get("buffer_reads_ps", 0),
                "buffer_hit_pct": latest.get("buffer_hit_pct", 0),
                "row_reads_ps": latest.get("row_reads_ps", 0),
                "row_writes_ps": latest.get("row_writes_ps", 0),
            },
            # Session states breakdown
            "session_states": {
                "total": latest.get("sessions_total", 0),
                "active": latest.get("sessions_active", 0),
                "idle": latest.get("sessions_idle", 0),
                "idle_tx": latest.get("sessions_idle_tx", 0),
            },
            "sessions": latest.get("sessions_table", []),
            "wait_events": latest.get("wait_events_table", []),
            "snapshots": len(data),
        }


class WebSession:
    """Web session with connection and dispatcher."""

    def __init__(
        self,
        session_id: str,
        conn: ConnectionManager,
        config: Config,
    ):
        self.id = session_id
        self.conn = conn
        self.config = config
        self.formatter = WebFormatter()
        self.dispatcher = Dispatcher(conn, config, self.formatter)
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    def dispatch(self, input: str) -> Dict:
        """Dispatch input and return JSON result."""
        self.last_activity = datetime.now()

        if not input.strip():
            return self.formatter.format_empty()

        result, skill = self.dispatcher.dispatch(input)

        # Convert SkillResult to JSON format
        if result.result_type == "empty":
            return self.formatter.format_empty()

        elif result.result_type == "exit":
            return self.formatter.format_exit(result.message or "Goodbye!")

        elif result.result_type == "table":
            if result.success:
                return self.formatter.format_table(
                    result.data or [],
                    None,
                    result.execution_time,
                )
            else:
                return self.formatter.format_error(result.error or "Unknown error")

        elif result.result_type == "health":
            items = result.data.get("items", [])
            overall = result.data.get("overall", "ok")
            return self.formatter.format_health_report(items, overall)

        elif result.result_type == "text":
            if result.success:
                if result.message:
                    return self.formatter.format_success(result.message)
                elif result.data:
                    return self.formatter.format_text(str(result.data))
                else:
                    return self.formatter.format_empty()
            else:
                return self.formatter.format_error(result.error or "Unknown error")

        elif result.result_type == "llm":
            return {
                "type": "llm",
                "question": result.data.get("question", ""),
                "success": result.success,
                "error": result.error,
            }

        elif result.result_type == "dbtop":
            # Format dbtop results for web
            return self.formatter.format_dbtop(result.data or [])

        else:
            # Unknown result type
            if result.success:
                return self.formatter.format_text(str(result.data))
            else:
                return self.formatter.format_error(result.error or "Unknown error")

    def disconnect(self) -> None:
        """Disconnect database connection."""
        if self.conn:
            self.conn.disconnect()

    def is_expired(self, max_age_minutes: int = 30) -> bool:
        """Check if session is expired."""
        age = (datetime.now() - self.last_activity).total_seconds()
        return age > max_age_minutes * 60

    def get_server_info(self) -> Dict:
        """Get server information."""
        try:
            info = self.conn.get_server_info()
            return {"success": True, "info": info}
        except Exception as e:
            return {"success": False, "error": str(e)}


def create_web_session(config: Config) -> WebSession:
    """Create a new web session."""
    session_id = uuid.uuid4().hex[:16]
    conn = create_connection_manager(config.database)
    return WebSession(session_id, conn, config)