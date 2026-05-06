"""PostgreSQL diagnostic SQL queries.

Predefined SQL templates for database monitoring and diagnostics.
"""

# Server and connection info
QUERIES = {
    # ==================== Server Info ====================
    "version": "SELECT version() as version",

    "uptime": """
        SELECT pg_postmaster_start_time() as start_time,
               EXTRACT(EPOCH FROM (now() - pg_postmaster_start_time())) as uptime_seconds
    """,

    # ==================== Sessions ====================
    "sessions_all": """
        SELECT pid, usename, application_name, client_addr, state,
               query_start, state_change, wait_event_type, wait_event,
               substring(query, 1, 100) as query_preview
        FROM pg_stat_activity
        WHERE datname = current_database()
        ORDER BY query_start DESC NULLS LAST
        LIMIT 100
    """,

    "sessions_active": """
        SELECT pid, usename, application_name, client_addr, state,
               query_start, wait_event_type, wait_event,
               substring(query, 1, 200) as query_preview,
               EXTRACT(EPOCH FROM (now() - query_start)) as duration_seconds
        FROM pg_stat_activity
        WHERE datname = current_database()
          AND state = 'active'
        ORDER BY query_start
    """,

    "sessions_idle": """
        SELECT pid, usename, application_name, client_addr, state,
               query_start, state_change,
               EXTRACT(EPOCH FROM (now() - state_change)) as idle_seconds
        FROM pg_stat_activity
        WHERE datname = current_database()
          AND state = 'idle'
          AND EXTRACT(EPOCH FROM (now() - state_change)) > 300  -- idle > 5min
        ORDER BY state_change
    """,

    "connection_count": """
        SELECT datname, count(*) as connections,
               count(*) FILTER (WHERE state = 'active') as active,
               count(*) FILTER (WHERE state = 'idle') as idle,
               count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_tx
        FROM pg_stat_activity
        GROUP BY datname
        ORDER BY connections DESC
    """,

    # ==================== Locks ====================
    "locks_all": """
        SELECT l.locktype, l.database, l.relation, l.page, l.tuple,
               l.virtualxid, l.transactionid, l.classid, l.objid, l.objsubid,
               l.virtualtransaction, l.pid, l.mode, l.granted,
               a.usename, a.query,
               substring(a.query, 1, 100) as query_preview
        FROM pg_locks l
        LEFT JOIN pg_stat_activity a ON l.pid = a.pid
        WHERE a.datname = current_database() OR a.datname IS NULL
        ORDER BY l.granted, l.pid
    """,

    "locks_blocked": """
        SELECT blocked.pid as blocked_pid,
               blocked.usename as blocked_user,
               substring(blocked.query, 1, 100) as blocked_query,
               blocking.pid as blocking_pid,
               blocking.usename as blocking_user,
               substring(blocking.query, 1, 100) as blocking_query,
               blocked_lock.mode as blocked_mode,
               blocking_lock.mode as blocking_mode
        FROM pg_stat_activity blocked
        JOIN pg_locks blocked_lock ON blocked.pid = blocked_lock.pid
        JOIN pg_locks blocking_lock ON blocked_lock.transactionid = blocking_lock.transactionid
            AND blocked_lock.pid != blocking_lock.pid
        JOIN pg_stat_activity blocking ON blocking_lock.pid = blocking.pid
        WHERE blocked_lock.granted = false
          AND blocking_lock.granted = true
          AND blocked.datname = current_database()
    """,

    "lock_tree": """
        WITH RECURSIVE lock_tree AS (
            -- Base: find blocking sessions
            SELECT
                blocked.pid as blocked_pid,
                blocking.pid as blocking_pid,
                blocked.usename as blocked_user,
                blocking.usename as blocking_user,
                substring(blocked.query, 1, 50) as blocked_query,
                substring(blocking.query, 1, 50) as blocking_query,
                1 as level,
                ARRAY[blocking.pid] as path
            FROM pg_stat_activity blocked
            JOIN pg_locks blocked_lock ON blocked.pid = blocked_lock.pid AND blocked_lock.granted = false
            JOIN pg_locks blocking_lock ON (
                blocked_lock.transactionid = blocking_lock.transactionid
                OR blocked_lock.relation = blocking_lock.relation
            ) AND blocked_lock.pid != blocking_lock.pid
            JOIN pg_stat_activity blocking ON blocking_lock.pid = blocking.pid AND blocking_lock.granted = true
            WHERE blocked.datname = current_database()

            UNION ALL

            -- Recursive: find chain
            SELECT
                lt.blocked_pid,
                lt.blocking_pid,
                lt.blocked_user,
                lt.blocking_user,
                lt.blocked_query,
                lt.blocking_query,
                lt.level + 1,
                lt.path || b.pid
            FROM lock_tree lt
            JOIN pg_locks blocked_lock ON lt.blocking_pid = blocked_lock.pid AND blocked_lock.granted = false
            JOIN pg_locks blocking_lock ON (
                blocked_lock.transactionid = blocking_lock.transactionid
                OR blocked_lock.relation = blocking_lock.relation
            ) AND blocked_lock.pid != blocking_lock.pid
            JOIN pg_stat_activity b ON blocking_lock.pid = b.pid AND blocking_lock.granted = true
            WHERE NOT b.pid = ANY(lt.path)
        )
        SELECT * FROM lock_tree ORDER BY level, path
    """,

    # ==================== Wait Events ====================
    "wait_events": """
        SELECT wait_event_type, wait_event, count(*) as count
        FROM pg_stat_activity
        WHERE datname = current_database()
          AND wait_event IS NOT NULL
          AND wait_event_type IS NOT NULL
        GROUP BY wait_event_type, wait_event
        ORDER BY count DESC
    """,

    "wait_events_active": """
        SELECT wait_event_type, wait_event, count(*) as count,
               array_agg(pid) as pids
        FROM pg_stat_activity
        WHERE datname = current_database()
          AND state = 'active'
          AND wait_event IS NOT NULL
        GROUP BY wait_event_type, wait_event
        ORDER BY count DESC
    """,

    # ==================== Space ====================
    "database_size": """
        SELECT datname,
               pg_database_size(datname) as size_bytes,
               pg_size_pretty(pg_database_size(datname)) as size_pretty
        FROM pg_database
        WHERE datistemplate = false
        ORDER BY pg_database_size(datname) DESC
    """,

    "table_sizes": """
        SELECT schemaname, relname,
               pg_relation_size(schemaname || '.' || relname) as table_size,
               pg_total_relation_size(schemaname || '.' || relname) as total_size,
               pg_size_pretty(pg_relation_size(schemaname || '.' || relname)) as table_size_pretty,
               pg_size_pretty(pg_total_relation_size(schemaname || '.' || relname)) as total_size_pretty
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(schemaname || '.' || relname) DESC
        LIMIT 20
    """,

    "index_sizes": """
        SELECT schemaname, relname as table_name, indexrelname as index_name,
               pg_relation_size(schemaname || '.' || indexrelname) as index_size,
               pg_size_pretty(pg_relation_size(schemaname || '.' || indexrelname)) as index_size_pretty,
               idx_scan as scans, idx_tup_read as tuples_read, idx_tup_fetch as tuples_fetch
        FROM pg_stat_user_indexes
        ORDER BY pg_relation_size(schemaname || '.' || indexrelname) DESC
        LIMIT 20
    """,

    "tablespace_info": """
        SELECT spcname as name,
               pg_size_pretty(pg_tablespace_size(spcname)) as size,
               spclocation as location
        FROM pg_tablespace
        WHERE spcname NOT IN ('pg_global', 'pg_default')
    """,

    # ==================== Vacuum ====================
    "vacuum_status": """
        SELECT schemaname, relname,
               n_dead_tup as dead_tuples,
               n_live_tup as live_tuples,
               round(100.0 * n_dead_tup / (n_live_tup + n_dead_tup + 1), 2) as dead_ratio,
               last_vacuum, last_autovacuum,
               vacuum_count, autovacuum_count
        FROM pg_stat_user_tables
        WHERE n_dead_tup > 0
        ORDER BY n_dead_tup DESC
        LIMIT 20
    """,

    "autovacuum_settings": """
        SELECT name, setting, unit, short_desc
        FROM pg_settings
        WHERE name LIKE '%autovacuum%'
        ORDER BY name
    """,

    # ==================== WAL ====================
    "wal_status": """
        SELECT pg_current_wal_lsn() as current_lsn,
               pg_walfile_name(pg_current_wal_lsn()) as current_wal_file,
               pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0') as wal_bytes,
               pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0')) as wal_size
    """,

    "wal_files": """
        SELECT name, size, modification
        FROM pg_ls_waldir()
        ORDER BY modification DESC
        LIMIT 10
    """,

    "wal_stats": """
        SELECT wal_records, wal_fpi, wal_bytes,
               pg_size_pretty(wal_bytes) as wal_bytes_pretty,
               wal_write, wal_write_time, wal_sync, wal_sync_time
        FROM pg_stat_wal
    """,

    # ==================== Replication ====================
    "replication_status": """
        SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
               pg_wal_lsn_diff(sent_lsn, replay_lsn) as lag_bytes,
               pg_size_pretty(pg_wal_lsn_diff(sent_lsn, replay_lsn)) as lag,
               sync_state, application_name
        FROM pg_stat_replication
    """,

    "replication_slots": """
        SELECT slot_name, slot_type, active, restart_lsn,
               pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) as retained_wal
        FROM pg_replication_slots
    """,

    # ==================== Long Transactions ====================
    "long_transactions": """
        SELECT pid, usename, application_name, client_addr,
               substring(query, 1, 100) as query_preview,
               EXTRACT(EPOCH FROM (now() - query_start)) as duration_seconds,
               state, wait_event_type, wait_event
        FROM pg_stat_activity
        WHERE datname = current_database()
          AND state IN ('active', 'idle in transaction', 'idle in transaction aborted')
          AND EXTRACT(EPOCH FROM (now() - query_start)) > 60
        ORDER BY query_start
    """,

    "idle_in_transaction": """
        SELECT pid, usename,
               substring(query, 1, 100) as query_preview,
               EXTRACT(EPOCH FROM (now() - state_change)) as idle_seconds,
               state
        FROM pg_stat_activity
        WHERE datname = current_database()
          AND state = 'idle in transaction'
          AND EXTRACT(EPOCH FROM (now() - state_change)) > 300
        ORDER BY state_change
    """,

    # ==================== Bloat ====================
    "bloat_estimate": """
        SELECT schemaname, relname as table_name,
               n_dead_tup as dead_tuples,
               n_live_tup as live_tuples,
               pg_relation_size(schemaname || '.' || relname) as table_size,
               round(100.0 * n_dead_tup / (n_live_tup + n_dead_tup + 1), 2) as bloat_ratio
        FROM pg_stat_user_tables
        WHERE n_dead_tup > 1000
          AND round(100.0 * n_dead_tup / (n_live_tup + n_dead_tup + 1), 2) > 10
        ORDER BY n_dead_tup DESC
        LIMIT 20
    """,

    # ==================== XID Wraparound ====================
    "xid_age": """
        SELECT datname,
               age(datfrozenxid) as xid_age,
               2147483647 - age(datfrozenxid) as remaining_xids,
               round(100.0 * age(datfrozenxid) / 2147483647, 2) as percent_used
        FROM pg_database
        WHERE datistemplate = false
        ORDER BY age(datfrozenxid) DESC
    """,

    "autovacuum_freeze": """
        SELECT schemaname, relname,
               age(relfrozenxid) as xid_age,
               n_dead_tup as dead_tuples,
               last_autovacuum
        FROM pg_stat_user_tables
        WHERE age(relfrozenxid) > 100000000
        ORDER BY age(relfrozenxid) DESC
    """,

    # ==================== Buffer Stats ====================
    "buffer_stats": """
        SELECT sum(blks_read) as blocks_read,
               sum(blks_hit) as blocks_hit,
               round(100.0 * sum(blks_hit) / (sum(blks_read) + sum(blks_hit) + 1), 2) as cache_hit_ratio
        FROM pg_stat_database
        WHERE datname = current_database()
    """,

    "shared_buffers_usage": """
        SELECT datname,
               blks_read, blks_hit,
               tup_returned, tup_fetched, tup_inserted, tup_updated, tup_deleted,
               xact_commit, xact_rollback,
               conflicts, deadlocks,
               temp_files, temp_bytes
        FROM pg_stat_database
        WHERE datname = current_database()
    """,

    # ==================== SQL Statistics ====================
    "slow_sql": """
        SELECT calls, total_exec_time / 1000 as total_time_ms,
               mean_exec_time / 1000 as mean_time_ms,
               min_exec_time / 1000 as min_time_ms,
               max_exec_time / 1000 as max_time_ms,
               rows, shared_blks_hit, shared_blks_read,
               substring(query, 1, 200) as query_preview
        FROM pg_stat_statements
        WHERE mean_exec_time > 1000  -- > 1 second average
        ORDER BY mean_exec_time DESC
        LIMIT 20
    """,

    "top_sql_time": """
        SELECT calls,
               round(total_exec_time / 1000, 2) as total_time_ms,
               round(mean_exec_time / 1000, 2) as mean_time_ms,
               rows,
               substring(query, 1, 100) as query_preview
        FROM pg_stat_statements
        ORDER BY total_exec_time DESC
        LIMIT 20
    """,

    "top_sql_calls": """
        SELECT calls,
               round(total_exec_time / 1000, 2) as total_time_ms,
               round(mean_exec_time / 1000, 2) as mean_time_ms,
               rows,
               substring(query, 1, 100) as query_preview
        FROM pg_stat_statements
        ORDER BY calls DESC
        LIMIT 20
    """,

    # ==================== Parameters ====================
    "params_all": """
        SELECT name, setting, unit, source, short_desc
        FROM pg_settings
        ORDER BY name
    """,

    "params_memory": """
        SELECT name, setting, unit, short_desc
        FROM pg_settings
        WHERE name IN ('shared_buffers', 'work_mem', 'maintenance_work_mem',
                       'effective_cache_size', 'huge_pages')
        ORDER BY name
    """,

    "params_checkpoint": """
        SELECT name, setting, unit, short_desc
        FROM pg_settings
        WHERE name LIKE '%checkpoint%' OR name LIKE '%wal%'
        ORDER BY name
    """,

    # ==================== Users ====================
    "users_all": """
        SELECT usename as username, valuntil as password_expiry,
               usecreatedb as can_create_db, usesuper as is_superuser
        FROM pg_user
        ORDER BY usename
    """,

    "roles": """
        SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin,
               rolconnlimit, rolvaliduntil
        FROM pg_roles
        ORDER BY rolname
    """,

    # ==================== Table Info ====================
    "table_info": """
        SELECT table_schema, table_name, column_name, data_type,
               is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name, ordinal_position
    """,

    "table_constraints": """
        SELECT tc.table_schema, tc.table_name, tc.constraint_name,
               tc.constraint_type, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY tc.table_schema, tc.table_name
    """,

    "table_indexes": """
        SELECT schemaname, relname as table_name, indexrelname as index_name,
               indisunique as is_unique, indisprimary as is_primary,
               pg_get_indexdef(indexrelid) as definition
        FROM pg_indexes
        JOIN pg_index ON pg_indexes.indexname = pg_index.indrelid::regclass::text
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, relname
    """,

    # ==================== Index Health ====================
    "unused_indexes": """
        SELECT schemaname, relname as table_name, indexrelname as index_name,
               idx_scan as scans, pg_size_pretty(pg_relation_size(indexrelid)) as size
        FROM pg_stat_user_indexes
        WHERE idx_scan = 0
          AND indexrelname NOT LIKE '%_pkey'
        ORDER BY pg_relation_size(indexrelid) DESC
        LIMIT 20
    """,

    "duplicate_indexes": """
        SELECT schemaname, relname as table_name,
               array_agg(indexrelname) as indexes,
               pg_get_indexdef(min(indexrelid)) as definition
        FROM pg_indexes
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        GROUP BY schemaname, relname, pg_get_indexdef(indexrelid)
        HAVING count(*) > 1
    """,

    # ==================== Health Check ====================
    "health_connections": """
        SELECT
            max_connections,
            (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) as current_connections,
            round(100.0 * (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) / max_connections, 2) as connection_pct
        FROM pg_settings WHERE name = 'max_connections'
    """,

    "health_deadlocks": """
        SELECT deadlocks
        FROM pg_stat_database
        WHERE datname = current_database()
    """,

    "health_cache_hit": """
        SELECT round(100.0 * blks_hit / (blks_read + blks_hit + 1), 2) as cache_hit_ratio
        FROM pg_stat_database
        WHERE datname = current_database()
    """,

    "health_transactions": """
        SELECT xact_commit, xact_rollback,
               round(100.0 * xact_rollback / (xact_commit + xact_rollback + 1), 2) as rollback_pct
        FROM pg_stat_database
        WHERE datname = current_database()
    """,

    "health_temp_files": """
        SELECT temp_files, pg_size_pretty(temp_bytes) as temp_bytes
        FROM pg_stat_database
        WHERE datname = current_database()
    """,
}

# SQL keywords for detecting SQL statements
SQL_KEYWORDS = [
    "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP",
    "TRUNCATE", "WITH", "BEGIN", "COMMIT", "ROLLBACK", "EXPLAIN", "ANALYZE",
    "SHOW", "SET", "GRANT", "REVOKE", "COPY", "VACUUM", "REINDEX",
]

# PostgreSQL error codes
PG_ERROR_CODES = {
    "00000": "successful_completion",
    "01000": "warning",
    "08000": "connection_exception",
    "08006": "connection_failure",
    "08001": "sqlclient_unable_to_establish_sqlconnection",
    "08004": "sqlserver_rejected_establishment_of_sqlconnection",
    "08007": "transaction_resolution_unknown",
    "08P01": "protocol_violation",
    "03000": "sql_statement_not_yet_complete",
    "42000": "syntax_error_or_access_rule_violation",
    "42601": "syntax_error",
    "42501": "insufficient_privilege",
    "42602": "invalid_name",
    "42622": "name_too_long",
    "42939": "reserved_name",
    "42804": "datatype_mismatch",
    "42P01": "undefined_table",
    "42P02": "undefined_parameter",
    "42703": "undefined_column",
    "42883": "undefined_function",
    "42P04": "duplicate_database",
    "42704": "undefined_object",
    "42710": "duplicate_object",
    "42701": "duplicate_column",
    "23000": "integrity_constraint_violation",
    "23001": "restrict_violation",
    "23502": "not_null_violation",
    "23503": "foreign_key_violation",
    "23505": "unique_violation",
    "23514": "check_violation",
    "40000": "transaction_rollback",
    "40001": "serialization_failure",
    "40002": "transaction_integrity_constraint_violation",
    "40003": "statement_completion_unknown",
    "40P01": "deadlock_detected",
    "53000": "insufficient_resources",
    "53100": "disk_full",
    "53200": "out_of_memory",
    "53300": "too_many_connections",
    "54000": "program_limit_exceeded",
    "55000": "object_not_in_prerequisite_state",
    "55006": "object_in_use",
    "55P02": "cant_change_runtime_param",
    "55P03": "lock_not_available",
    "57000": "operator_intervention",
    "57014": "query_canceled",
    "57P01": "admin_shutdown",
    "57P02": "crash_shutdown",
    "57P03": "cannot_connect_now",
    "57P04": "database_dropped",
}


def get_query(name: str) -> str:
    """Get a predefined query by name."""
    return QUERIES.get(name, "")


def is_sql_statement(input: str) -> bool:
    """Check if input looks like a SQL statement."""
    first_word = input.strip().split()[0].upper() if input.strip() else ""
    return first_word in SQL_KEYWORDS