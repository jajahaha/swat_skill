"""LLM function calling tools."""

from typing import Any, Dict, List

from ..database.connection import ConnectionManager
from ..database.queries import get_query


def build_tools() -> List[Dict]:
    """Build tool definitions for Claude function calling."""
    return [
        {
            "name": "query_health",
            "description": "获取数据库整体健康状态，包括连接数、缓存命中率、事务状态等",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "query_sessions",
            "description": "获取活跃的数据库会话信息",
            "input_schema": {
                "type": "object",
                "properties": {
                    "active_only": {
                        "type": "boolean",
                        "description": "是否只返回活跃会话",
                    }
                },
            },
        },
        {
            "name": "query_waits",
            "description": "获取等待事件统计",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "query_locks",
            "description": "获取锁阻塞信息",
            "input_schema": {
                "type": "object",
                "properties": {
                    "blocked_only": {
                        "type": "boolean",
                        "description": "是否只返回被阻塞的锁",
                    }
                },
            },
        },
        {
            "name": "query_space",
            "description": "获取数据库和表空间使用情况",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "query_slowsql",
            "description": "获取慢SQL统计（需要pg_stat_statements扩展）",
            "input_schema": {
                "type": "object",
                "properties": {
                    "threshold_ms": {
                        "type": "integer",
                        "description": "慢SQL阈值（毫秒）",
                    }
                },
            },
        },
        {
            "name": "execute_sql",
            "description": "执行自定义SQL查询（只读查询）",
            "input_schema": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的SQL查询语句",
                    }
                },
                "required": ["sql"],
            },
        },
        {
            "name": "get_server_info",
            "description": "获取PostgreSQL服务器版本和基本信息",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "query_vacuum",
            "description": "获取Vacuum状态和需要清理的表",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "query_replication",
            "description": "获取复制状态",
            "input_schema": {"type": "object", "properties": {}},
        },
    ]


def execute_tool(
    conn: ConnectionManager,
    tool_name: str,
    tool_input: Dict[str, Any],
) -> Any:
    """Execute a tool and return result.

    Args:
        conn: Database connection manager.
        tool_name: Tool name to execute.
        tool_input: Tool input parameters.

    Returns:
        Tool execution result.
    """
    if tool_name == "query_health":
        result = conn.execute(get_query("health_connections"))
        if result.success:
            return result.rows
        return {"error": result.error}

    elif tool_name == "query_sessions":
        active_only = tool_input.get("active_only", False)
        if active_only:
            result = conn.execute(get_query("sessions_active"))
        else:
            result = conn.execute(get_query("sessions_all"))
        if result.success:
            return result.rows
        return {"error": result.error}

    elif tool_name == "query_waits":
        result = conn.execute(get_query("wait_events"))
        if result.success:
            return result.rows
        return {"error": result.error}

    elif tool_name == "query_locks":
        blocked_only = tool_input.get("blocked_only", False)
        if blocked_only:
            result = conn.execute(get_query("locks_blocked"))
        else:
            result = conn.execute(get_query("locks_all"))
        if result.success:
            return result.rows
        return {"error": result.error}

    elif tool_name == "query_space":
        result = conn.execute(get_query("database_size"))
        if result.success:
            return result.rows
        return {"error": result.error}

    elif tool_name == "query_slowsql":
        threshold_ms = tool_input.get("threshold_ms", 1000)
        result = conn.execute(get_query("slow_sql"))
        if result.success:
            # Filter by threshold
            filtered = [
                row for row in result.rows
                if float(row.get("mean_time_ms", 0)) >= threshold_ms
            ]
            return filtered
        return {"error": result.error}

    elif tool_name == "execute_sql":
        sql = tool_input.get("sql", "")
        if not sql:
            return {"error": "No SQL provided"}

        # Security check: only allow SELECT queries
        if not sql.strip().upper().startswith("SELECT"):
            return {"error": "Only SELECT queries are allowed for safety"}

        result = conn.execute(sql)
        if result.success:
            return result.rows
        return {"error": result.error}

    elif tool_name == "get_server_info":
        return conn.get_server_info()

    elif tool_name == "query_vacuum":
        result = conn.execute(get_query("vacuum_status"))
        if result.success:
            return result.rows
        return {"error": result.error}

    elif tool_name == "query_replication":
        result = conn.execute(get_query("replication_status"))
        if result.success:
            return result.rows
        return {"error": result.error}

    else:
        return {"error": f"Unknown tool: {tool_name}"}