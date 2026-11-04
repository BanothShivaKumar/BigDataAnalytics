"""
Module 3: Apache Cassandra Database Manager
Handles cluster connection, keyspace and table provisioning, prepared statement
execution, atomic counter updates, query execution, and graceful teardown.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import date, datetime
import pandas as pd

# Handle Python 3.12+ compatibility for cassandra-driver (asyncore polyfill)
try:
    import asyncore
except ImportError:
    try:
        import pyasyncore
        sys.modules["asyncore"] = pyasyncore
    except ImportError:
        pass

from cassandra.cluster import Cluster, Session, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.query import PreparedStatement, SimpleStatement, ConsistencyLevel
from cassandra.policies import DCAwareRoundRobinPolicy, RetryPolicy

# Configure module logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CassandraManager")


class CassandraManager:
    """Manages Apache Cassandra cluster connection, schema lifecycle, and CQL operations."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9042,
        keyspace: str = "web_analytics",
        replication_factor: int = 1,
        connect_timeout: float = 8.0,
    ):
        self.host = os.getenv("CASSANDRA_HOST", host)
        self.port = int(os.getenv("CASSANDRA_PORT", port))
        self.keyspace = os.getenv("CASSANDRA_KEYSPACE", keyspace)
        self.replication_factor = int(os.getenv("CASSANDRA_REPLICATION_FACTOR", replication_factor))
        self.connect_timeout = connect_timeout

        self.cluster: Optional[Cluster] = None
        self.session: Optional[Session] = None
        self.is_connected: bool = False

        # Prepared statements cache
        self.prep_insert_logs_by_date: Optional[PreparedStatement] = None
        self.prep_insert_logs_by_ip: Optional[PreparedStatement] = None
        self.prep_insert_logs_by_status: Optional[PreparedStatement] = None
        self.prep_update_url_counter: Optional[PreparedStatement] = None
        self.prep_insert_slow_requests: Optional[PreparedStatement] = None

    def connect(self) -> Tuple[bool, str]:
        """
        Establish connection to the local Apache Cassandra cluster.

        Returns:
            (success_bool, message_str)
        """
        try:
            profile = ExecutionProfile(
                load_balancing_policy=DCAwareRoundRobinPolicy(local_dc="datacenter1"),
                retry_policy=RetryPolicy(),
                consistency_level=ConsistencyLevel.LOCAL_ONE,
                request_timeout=15.0,
            )

            self.cluster = Cluster(
                contact_points=[self.host],
                port=self.port,
                connect_timeout=self.connect_timeout,
                execution_profiles={EXEC_PROFILE_DEFAULT: profile},
                protocol_version=4,
            )

            # Connect without keyspace first so we can initialize it if missing
            self.session = self.cluster.connect()
            self.is_connected = True
            logger.info("Connected to Cassandra at %s:%d", self.host, self.port)

            # Ensure keyspace exists and set current keyspace
            self._create_keyspace()
            self.session.set_keyspace(self.keyspace)

            # Ensure schema tables exist and prepare statements
            self._create_tables()
            self._prepare_statements()

            return True, f"Successfully connected to Apache Cassandra at {self.host}:{self.port}"
        except Exception as e:
            self.is_connected = False
            error_msg = f"Failed to connect to Apache Cassandra at {self.host}:{self.port} - {type(e).__name__}: {e}"
            logger.error(error_msg)
            return False, error_msg

    def _create_keyspace(self) -> None:
        """Create the keyspace if it does not already exist."""
        if not self.session:
            return
        cql = f"""
        CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
        WITH replication = {{
            'class': 'SimpleStrategy',
            'replication_factor': {self.replication_factor}
        }};
        """
        self.session.execute(cql)
        logger.info("Keyspace '%s' verified/created with replication_factor=%d", self.keyspace, self.replication_factor)

    def _create_tables(self) -> None:
        """Create all five required Cassandra tables."""
        if not self.session:
            return

        table_queries = [
            # 1. logs_by_date
            """
            CREATE TABLE IF NOT EXISTS logs_by_date (
                log_date date,
                hour_bucket int,
                event_time timestamp,
                log_id uuid,
                ip_address text,
                http_method text,
                url_path text,
                status_code int,
                response_time_ms double,
                user_agent text,
                request_size_bytes int,
                response_size_bytes int,
                PRIMARY KEY ((log_date, hour_bucket), event_time, log_id)
            ) WITH CLUSTERING ORDER BY (event_time DESC, log_id ASC);
            """,
            # 2. logs_by_ip
            """
            CREATE TABLE IF NOT EXISTS logs_by_ip (
                ip_address text,
                log_date date,
                event_time timestamp,
                log_id uuid,
                http_method text,
                url_path text,
                status_code int,
                response_time_ms double,
                user_agent text,
                request_size_bytes int,
                response_size_bytes int,
                PRIMARY KEY ((ip_address, log_date), event_time, log_id)
            ) WITH CLUSTERING ORDER BY (event_time DESC, log_id ASC);
            """,
            # 3. logs_by_status
            """
            CREATE TABLE IF NOT EXISTS logs_by_status (
                log_date date,
                status_code int,
                event_time timestamp,
                log_id uuid,
                ip_address text,
                http_method text,
                url_path text,
                response_time_ms double,
                user_agent text,
                request_size_bytes int,
                response_size_bytes int,
                PRIMARY KEY ((log_date, status_code), event_time, log_id)
            ) WITH CLUSTERING ORDER BY (event_time DESC, log_id ASC);
            """,
            # 4. url_daily_counts
            """
            CREATE TABLE IF NOT EXISTS url_daily_counts (
                log_date date,
                url_path text,
                status_code int,
                request_count counter,
                PRIMARY KEY ((log_date), url_path, status_code)
            );
            """,
            # 5. slow_requests_by_date
            """
            CREATE TABLE IF NOT EXISTS slow_requests_by_date (
                log_date date,
                hour_bucket int,
                response_time_ms double,
                event_time timestamp,
                log_id uuid,
                ip_address text,
                http_method text,
                url_path text,
                status_code int,
                user_agent text,
                request_size_bytes int,
                response_size_bytes int,
                PRIMARY KEY ((log_date, hour_bucket), response_time_ms, event_time, log_id)
            ) WITH CLUSTERING ORDER BY (response_time_ms DESC, event_time DESC, log_id ASC);
            """
        ]

        for query in table_queries:
            self.session.execute(query)

        logger.info("All 5 required tables verified/created successfully.")

    def _prepare_statements(self) -> None:
        """Prepare CQL statements for high-throughput parameterized insertions."""
        if not self.session:
            return

        self.prep_insert_logs_by_date = self.session.prepare("""
            INSERT INTO logs_by_date (
                log_date, hour_bucket, event_time, log_id, ip_address,
                http_method, url_path, status_code, response_time_ms,
                user_agent, request_size_bytes, response_size_bytes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        self.prep_insert_logs_by_ip = self.session.prepare("""
            INSERT INTO logs_by_ip (
                ip_address, log_date, event_time, log_id,
                http_method, url_path, status_code, response_time_ms,
                user_agent, request_size_bytes, response_size_bytes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        self.prep_insert_logs_by_status = self.session.prepare("""
            INSERT INTO logs_by_status (
                log_date, status_code, event_time, log_id,
                ip_address, http_method, url_path, response_time_ms,
                user_agent, request_size_bytes, response_size_bytes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        self.prep_update_url_counter = self.session.prepare("""
            UPDATE url_daily_counts
            SET request_count = request_count + 1
            WHERE log_date = ? AND url_path = ? AND status_code = ?
        """)

        self.prep_insert_slow_requests = self.session.prepare("""
            INSERT INTO slow_requests_by_date (
                log_date, hour_bucket, response_time_ms, event_time, log_id,
                ip_address, http_method, url_path, status_code,
                user_agent, request_size_bytes, response_size_bytes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        logger.info("Prepared statements compiled successfully.")

    def insert_batch(
        self,
        cleaned_df: pd.DataFrame,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Insert preprocessed log records across all relevant tables.
        Uses prepared statements with per-record multi-table dispatch.

        Returns:
            Dict containing success_count, failure_count, errors
        """
        if not self.is_connected or not self.session:
            raise RuntimeError("Cannot insert: Cassandra is not connected.")

        total_rows = len(cleaned_df)
        success_count = 0
        failure_count = 0
        errors: List[str] = []

        for idx, (_, row) in enumerate(cleaned_df.iterrows()):
            try:
                # 1. Insert into logs_by_date
                self.session.execute(self.prep_insert_logs_by_date, (
                    row["log_date"],
                    int(row["hour_bucket"]),
                    row["event_time"],
                    row["log_id"],
                    row["ip_address"],
                    row["http_method"],
                    row["url_path"],
                    int(row["status_code"]),
                    float(row["response_time_ms"]),
                    row["user_agent"],
                    int(row["request_size_bytes"]),
                    int(row["response_size_bytes"]),
                ))

                # 2. Insert into logs_by_ip
                self.session.execute(self.prep_insert_logs_by_ip, (
                    row["ip_address"],
                    row["log_date"],
                    row["event_time"],
                    row["log_id"],
                    row["http_method"],
                    row["url_path"],
                    int(row["status_code"]),
                    float(row["response_time_ms"]),
                    row["user_agent"],
                    int(row["request_size_bytes"]),
                    int(row["response_size_bytes"]),
                ))

                # 3. Insert into logs_by_status
                self.session.execute(self.prep_insert_logs_by_status, (
                    row["log_date"],
                    int(row["status_code"]),
                    row["event_time"],
                    row["log_id"],
                    row["ip_address"],
                    row["http_method"],
                    row["url_path"],
                    float(row["response_time_ms"]),
                    row["user_agent"],
                    int(row["request_size_bytes"]),
                    int(row["response_size_bytes"]),
                ))

                # 4. Atomic increment in url_daily_counts
                self.session.execute(self.prep_update_url_counter, (
                    row["log_date"],
                    row["url_path"],
                    int(row["status_code"]),
                ))

                # 5. Insert into slow_requests_by_date if latency >= 500ms
                if row.get("is_slow", False) or row["response_time_ms"] >= 500.0:
                    self.session.execute(self.prep_insert_slow_requests, (
                        row["log_date"],
                        int(row["hour_bucket"]),
                        float(row["response_time_ms"]),
                        row["event_time"],
                        row["log_id"],
                        row["ip_address"],
                        row["http_method"],
                        row["url_path"],
                        int(row["status_code"]),
                        row["user_agent"],
                        int(row["request_size_bytes"]),
                        int(row["response_size_bytes"]),
                    ))

                success_count += 1
            except Exception as e:
                failure_count += 1
                if len(errors) < 5:
                    errors.append(str(e))

            if progress_callback and (idx + 1) % 100 == 0 or (idx + 1) == total_rows:
                progress_callback(idx + 1, total_rows)

        return {
            "total": total_rows,
            "success": success_count,
            "failure": failure_count,
            "errors": errors,
        }

    def execute_query(self, cql: str, parameters=None) -> List[Any]:
        """Execute arbitrary CQL query and return list of row results."""
        if not self.is_connected or not self.session:
            raise RuntimeError("Cassandra is not connected.")
        if parameters:
            statement = SimpleStatement(cql, consistency_level=ConsistencyLevel.LOCAL_ONE)
            return list(self.session.execute(statement, parameters))
        return list(self.session.execute(cql))

    def get_cluster_info(self) -> Dict[str, Any]:
        """Fetch metadata about connected cluster and keyspace."""
        if not self.is_connected or not self.cluster or not self.session:
            return {"connected": False}

        try:
            metadata = self.cluster.metadata
            row = self.session.execute("SELECT release_version, cluster_name FROM system.local").one()
            release_version = row.release_version if row else "Unknown"
            cluster_name = row.cluster_name if row else metadata.cluster_name

            tables = []
            if self.keyspace in metadata.keyspaces:
                tables = list(metadata.keyspaces[self.keyspace].tables.keys())

            return {
                "connected": True,
                "host": self.host,
                "port": self.port,
                "cluster_name": cluster_name,
                "release_version": release_version,
                "keyspace": self.keyspace,
                "replication_factor": self.replication_factor,
                "tables": sorted(tables),
                "endpoints": [h.address for h in metadata.all_hosts()],
            }
        except Exception as e:
            logger.error("Error reading cluster metadata: %s", e)
            return {"connected": False, "error": str(e)}

    def close(self) -> None:
        """Gracefully shutdown session and cluster connections."""
        if self.session and not self.session.is_shutdown:
            self.session.shutdown()
        if self.cluster and not self.cluster.is_shutdown:
            self.cluster.shutdown()
        self.is_connected = False
        logger.info("Cassandra connection closed.")


if __name__ == "__main__":
    mgr = CassandraManager()
    ok, msg = mgr.connect()
    print("Connect result:", ok, msg)
    if ok:
        info = mgr.get_cluster_info()
        print("Cluster Info:", info)
        mgr.close()

