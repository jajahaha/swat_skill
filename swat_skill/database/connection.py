"""PostgreSQL connection management.

Provides connection pool and query execution utilities.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple

import psycopg
from psycopg.rows import dict_row

from ..config import DatabaseConfig


@dataclass
class QueryResult:
    """Result of a SQL query execution."""

    rows: List[Dict[str, Any]]
    rowcount: int
    columns: List[str]
    execution_time: float  # seconds
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def empty(self) -> bool:
        return len(self.rows) == 0


class ConnectionManager:
    """Manages PostgreSQL connections and query execution."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection: Optional[psycopg.Connection] = None
        self._last_activity: float = 0.0

    def connect(self) -> None:
        """Establish database connection."""
        if self._connection is not None and not self._connection.closed:
            return

        conn_info = self.config.get_connection_info()
        self._connection = psycopg.connect(
            **conn_info,
            row_factory=dict_row,
            autocommit=True,  # Auto-commit for read queries
        )
        self._last_activity = time.time()

    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
        self._connection = None

    def is_connected(self) -> bool:
        """Check if connection is active."""
        if self._connection is None:
            return False
        if self._connection.closed:
            return False
        return True

    def ping(self) -> bool:
        """Test connection health."""
        try:
            self.execute("SELECT 1")
            return True
        except Exception:
            return False

    def reconnect(self) -> bool:
        """Reconnect if connection is lost."""
        self.disconnect()
        try:
            self.connect()
            return True
        except Exception:
            return False

    def execute(
        self,
        sql: str,
        params: Optional[Tuple] = None,
    ) -> QueryResult:
        """Execute a SQL query and return results.

        Args:
            sql: SQL query string.
            params: Optional query parameters.

        Returns:
            QueryResult with rows and metadata.
        """
        start_time = time.time()

        try:
            if not self.is_connected():
                self.connect()

            with self._connection.cursor() as cur:
                cur.execute(sql, params)

                # Check if query returns rows
                if cur.description:
                    rows = cur.fetchall()
                    columns = [desc.name for desc in cur.description]
                    rowcount = len(rows)
                else:
                    rows = []
                    columns = []
                    rowcount = cur.rowcount

            execution_time = time.time() - start_time
            self._last_activity = time.time()

            return QueryResult(
                rows=rows,
                rowcount=rowcount,
                columns=columns,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return QueryResult(
                rows=[],
                rowcount=0,
                columns=[],
                execution_time=execution_time,
                error=str(e),
            )

    def execute_transaction(
        self,
        statements: List[Tuple[str, Optional[Tuple]]],
    ) -> List[QueryResult]:
        """Execute multiple statements in a transaction.

        Args:
            statements: List of (sql, params) tuples.

        Returns:
            List of QueryResult for each statement.
        """
        results = []

        try:
            if not self.is_connected():
                self.connect()

            # Start transaction
            with self._connection.transaction():
                for sql, params in statements:
                    result = self.execute(sql, params)
                    results.append(result)
                    if not result.success:
                        # Transaction will rollback automatically
                        break

            return results

        except Exception as e:
            # Return error for all statements
            return [
                QueryResult(
                    rows=[], rowcount=0, columns=[], execution_time=0.0, error=str(e)
                )
                for _ in statements
            ]

    @contextmanager
    def get_cursor(self) -> Iterator[psycopg.Cursor]:
        """Get a cursor for manual query execution."""
        if not self.is_connected():
            self.connect()

        cursor = self._connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def get_server_info(self) -> Dict[str, Any]:
        """Get PostgreSQL server information."""
        result = self.execute("SELECT version()")
        if result.success and result.rows:
            version_str = result.rows[0].get("version", "")
            return {
                "version": version_str,
                "connected": True,
            }
        return {"version": "", "connected": False}

    def get_database_size(self) -> Optional[int]:
        """Get current database size in bytes."""
        result = self.execute(
            "SELECT pg_database_size(current_database()) as size"
        )
        if result.success and result.rows:
            return result.rows[0].get("size")
        return None

    def get_connection_count(self) -> int:
        """Get number of connections to current database."""
        result = self.execute(
            "SELECT count(*) as count FROM pg_stat_activity "
            "WHERE datname = current_database()"
        )
        if result.success and result.rows:
            return result.rows[0].get("count", 0)
        return 0


def create_connection_manager(config: DatabaseConfig) -> ConnectionManager:
    """Factory function to create ConnectionManager."""
    manager = ConnectionManager(config)
    manager.connect()
    return manager