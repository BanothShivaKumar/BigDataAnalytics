"""
Module 4: Query-Based Analytics Engine
Retrieves data from Apache Cassandra using query-driven patterns and computes
comprehensive Big Data analytical metrics, latency percentiles, error rates,
and traffic distributions.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from cassandra_manager import CassandraManager


class AnalyticsEngine:
    """Analytical engine performing statistical calculations on Cassandra log data."""

    def __init__(self, db_manager: CassandraManager, slow_threshold_ms: float = 500.0):
        self.db = db_manager
        self.slow_threshold_ms = slow_threshold_ms

    def get_available_dates(self) -> List[date]:
        """
        Retrieve distinct dates present in url_daily_counts or logs_by_date.
        Uses Cassandra partition scan on url_daily_counts.
        """
        if not self.db.is_connected:
            return []
        try:
            rows = self.db.execute_query("SELECT DISTINCT log_date FROM url_daily_counts")
            dates = [r.log_date for r in rows if r.log_date is not None]
            # Convert cassandra Date to python date if necessary
            py_dates = []
            for d in dates:
                if hasattr(d, "date"):
                    py_dates.append(d.date())
                elif isinstance(d, date):
                    py_dates.append(d)
                else:
                    try:
                        py_dates.append(pd.to_datetime(str(d)).date())
                    except Exception:
                        pass
            return sorted(list(set(py_dates)), reverse=True)
        except Exception:
            return []

    def fetch_logs_for_date(
        self,
        target_date: date,
        hour_bucket: Optional[int] = None,
        limit_per_bucket: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Query logs_by_date for a given date.
        Iterates over hour buckets (0..23) ensuring deterministic partition keys.
        """
        if not self.db.is_connected:
            return pd.DataFrame()

        hours = [hour_bucket] if hour_bucket is not None else list(range(24))
        all_rows = []

        query = """
            SELECT log_date, hour_bucket, event_time, log_id, ip_address,
                   http_method, url_path, status_code, response_time_ms,
                   user_agent, request_size_bytes, response_size_bytes
            FROM logs_by_date
            WHERE log_date = %s AND hour_bucket = %s
        """
        if limit_per_bucket:
            query += f" LIMIT {limit_per_bucket}"

        for h in hours:
            try:
                rows = self.db.execute_query(query, (target_date, h))
                for r in rows:
                    all_rows.append({
                        "log_date": r.log_date,
                        "hour_bucket": r.hour_bucket,
                        "event_time": r.event_time,
                        "log_id": str(r.log_id),
                        "ip_address": r.ip_address,
                        "http_method": r.http_method,
                        "url_path": r.url_path,
                        "status_code": r.status_code,
                        "response_time_ms": float(r.response_time_ms),
                        "user_agent": r.user_agent,
                        "request_size_bytes": r.request_size_bytes,
                        "response_size_bytes": r.response_size_bytes,
                    })
            except Exception as e:
                # Hour bucket may be empty
                continue

        df = pd.DataFrame(all_rows)
        if not df.empty:
            df["event_time"] = pd.to_datetime(df["event_time"])
            df = df.sort_values("event_time", ascending=False).reset_index(drop=True)
        return df

    def fetch_url_daily_counts(self, target_date: date) -> pd.DataFrame:
        """Query url_daily_counts partition for aggregated request statistics."""
        if not self.db.is_connected:
            return pd.DataFrame()

        query = """
            SELECT log_date, url_path, status_code, request_count
            FROM url_daily_counts
            WHERE log_date = %s
        """
        try:
            rows = self.db.execute_query(query, (target_date,))
            data = [{
                "log_date": r.log_date,
                "url_path": r.url_path,
                "status_code": r.status_code,
                "request_count": r.request_count,
            } for r in rows]
            return pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()

    def fetch_slow_requests(
        self,
        target_date: date,
        hour_bucket: Optional[int] = None,
        limit: int = 200
    ) -> pd.DataFrame:
        """Query slow_requests_by_date table ordered by response_time_ms DESC."""
        if not self.db.is_connected:
            return pd.DataFrame()

        hours = [hour_bucket] if hour_bucket is not None else list(range(24))
        all_slow = []

        query = """
            SELECT log_date, hour_bucket, response_time_ms, event_time, log_id,
                   ip_address, http_method, url_path, status_code, user_agent,
                   request_size_bytes, response_size_bytes
            FROM slow_requests_by_date
            WHERE log_date = %s AND hour_bucket = %s
            LIMIT %s
        """
        for h in hours:
            try:
                rows = self.db.execute_query(query, (target_date, h, limit))
                for r in rows:
                    all_slow.append({
                        "log_date": r.log_date,
                        "hour_bucket": r.hour_bucket,
                        "response_time_ms": float(r.response_time_ms),
                        "event_time": r.event_time,
                        "log_id": str(r.log_id),
                        "ip_address": r.ip_address,
                        "http_method": r.http_method,
                        "url_path": r.url_path,
                        "status_code": r.status_code,
                        "user_agent": r.user_agent,
                        "request_size_bytes": r.request_size_bytes,
                        "response_size_bytes": r.response_size_bytes,
                    })
            except Exception:
                continue

        df = pd.DataFrame(all_slow)
        if not df.empty:
            df = df.sort_values("response_time_ms", ascending=False).reset_index(drop=True)
            if limit:
                df = df.head(limit)
        return df

    def fetch_logs_by_status(
        self,
        target_date: date,
        status_code: int,
        limit: int = 200
    ) -> pd.DataFrame:
        """Query logs_by_status for specific status codes (e.g. 500, 404)."""
        if not self.db.is_connected:
            return pd.DataFrame()

        query = """
            SELECT log_date, status_code, event_time, log_id, ip_address,
                   http_method, url_path, response_time_ms, user_agent,
                   request_size_bytes, response_size_bytes
            FROM logs_by_status
            WHERE log_date = %s AND status_code = %s
            LIMIT %s
        """
        try:
            rows = self.db.execute_query(query, (target_date, status_code, limit))
            data = [{
                "log_date": r.log_date,
                "status_code": r.status_code,
                "event_time": r.event_time,
                "log_id": str(r.log_id),
                "ip_address": r.ip_address,
                "http_method": r.http_method,
                "url_path": r.url_path,
                "response_time_ms": float(r.response_time_ms),
                "user_agent": r.user_agent,
                "request_size_bytes": r.request_size_bytes,
                "response_size_bytes": r.response_size_bytes,
            } for r in rows]
            df = pd.DataFrame(data)
            if not df.empty:
                df["event_time"] = pd.to_datetime(df["event_time"])
            return df
        except Exception:
            return pd.DataFrame()

    def fetch_logs_by_ip(
        self,
        ip_address: str,
        target_date: date,
        limit: int = 200
    ) -> pd.DataFrame:
        """Query logs_by_ip for forensic analysis on a specific IP."""
        if not self.db.is_connected:
            return pd.DataFrame()

        query = """
            SELECT ip_address, log_date, event_time, log_id, http_method,
                   url_path, status_code, response_time_ms, user_agent,
                   request_size_bytes, response_size_bytes
            FROM logs_by_ip
            WHERE ip_address = %s AND log_date = %s
            LIMIT %s
        """
        try:
            rows = self.db.execute_query(query, (ip_address, target_date, limit))
            data = [{
                "ip_address": r.ip_address,
                "log_date": r.log_date,
                "event_time": r.event_time,
                "log_id": str(r.log_id),
                "http_method": r.http_method,
                "url_path": r.url_path,
                "status_code": r.status_code,
                "response_time_ms": float(r.response_time_ms),
                "user_agent": r.user_agent,
                "request_size_bytes": r.request_size_bytes,
                "response_size_bytes": r.response_size_bytes,
            } for r in rows]
            df = pd.DataFrame(data)
            if not df.empty:
                df["event_time"] = pd.to_datetime(df["event_time"])
            return df
        except Exception:
            return pd.DataFrame()

    # =========================================================================
    # Analytical Calculations (Pure Data Science Functions)
    # =========================================================================

    def compute_overview_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute top-level summary metrics from log DataFrame."""
        if df.empty:
            return {
                "total_requests": 0,
                "unique_ips": 0,
                "avg_response_time": 0.0,
                "min_response_time": 0.0,
                "max_response_time": 0.0,
                "median_response_time": 0.0,
                "p95_response_time": 0.0,
                "slow_requests_count": 0,
                "slow_requests_pct": 0.0,
                "success_count": 0,
                "success_rate": 0.0,
                "client_errors_count": 0,
                "server_errors_count": 0,
                "error_rate": 0.0,
            }

        total = len(df)
        unique_ips = df["ip_address"].nunique()
        latencies = df["response_time_ms"]

        avg_latency = float(latencies.mean())
        min_latency = float(latencies.min())
        max_latency = float(latencies.max())
        median_latency = float(latencies.median())
        p95_latency = float(np.percentile(latencies, 95))

        slow_count = int((latencies >= self.slow_threshold_ms).sum())
        slow_pct = round((slow_count / total) * 100, 2) if total > 0 else 0.0

        status_codes = df["status_code"]
        success_count = int(((status_codes >= 200) & (status_codes < 300)).sum())
        client_errors = int(((status_codes >= 400) & (status_codes < 500)).sum())
        server_errors = int(((status_codes >= 500) & (status_codes < 600)).sum())
        total_errors = client_errors + server_errors

        success_rate = round((success_count / total) * 100, 2) if total > 0 else 0.0
        error_rate = round((total_errors / total) * 100, 2) if total > 0 else 0.0

        return {
            "total_requests": total,
            "unique_ips": unique_ips,
            "avg_response_time": round(avg_latency, 2),
            "min_response_time": round(min_latency, 2),
            "max_response_time": round(max_latency, 2),
            "median_response_time": round(median_latency, 2),
            "p95_response_time": round(p95_latency, 2),
            "slow_requests_count": slow_count,
            "slow_requests_pct": slow_pct,
            "success_count": success_count,
            "success_rate": success_rate,
            "client_errors_count": client_errors,
            "server_errors_count": server_errors,
            "error_rate": error_rate,
        }

    @staticmethod
    def compute_hourly_traffic(df: pd.DataFrame) -> pd.DataFrame:
        """Compute traffic volume per hour (0 to 23)."""
        all_hours = pd.DataFrame({"hour": list(range(24))})
        if df.empty:
            all_hours["request_count"] = 0
            return all_hours

        if "hour_bucket" in df.columns:
            counts = df.groupby("hour_bucket").size().reset_index(name="request_count")
            merged = pd.merge(all_hours, counts, left_on="hour", right_on="hour_bucket", how="left")
            merged["request_count"] = merged["request_count"].fillna(0).astype(int)
            return merged[["hour", "request_count"]]
        else:
            return all_hours

    @staticmethod
    def compute_status_distribution(df: pd.DataFrame) -> pd.DataFrame:
        """Compute count and percentage distribution of HTTP status codes."""
        if df.empty:
            return pd.DataFrame(columns=["status_code", "count", "percentage", "category"])

        counts = df["status_code"].value_counts().reset_index()
        counts.columns = ["status_code", "count"]
        total = counts["count"].sum()
        counts["percentage"] = (counts["count"] / total * 100).round(2)

        def categorize_status(code: int) -> str:
            if 200 <= code < 300:
                return "2xx Success"
            elif 300 <= code < 400:
                return "3xx Redirection"
            elif 400 <= code < 500:
                return "4xx Client Error"
            elif 500 <= code < 600:
                return "5xx Server Error"
            return "Other"

        counts["category"] = counts["status_code"].apply(categorize_status)
        return counts.sort_values("count", ascending=False).reset_index(drop=True)

    @staticmethod
    def compute_method_distribution(df: pd.DataFrame) -> pd.DataFrame:
        """Compute breakdown of HTTP methods."""
        if df.empty:
            return pd.DataFrame(columns=["http_method", "count", "percentage"])
        counts = df["http_method"].value_counts().reset_index()
        counts.columns = ["http_method", "count"]
        counts["percentage"] = (counts["count"] / counts["count"].sum() * 100).round(2)
        return counts

    @staticmethod
    def compute_top_endpoints(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
        """Compute top requested URL paths with latency and error metrics."""
        if df.empty:
            return pd.DataFrame(columns=["url_path", "requests", "avg_latency_ms", "errors", "error_rate_pct"])

        grouped = df.groupby("url_path").agg(
            requests=("log_id", "count"),
            avg_latency_ms=("response_time_ms", "mean"),
            p95_latency_ms=("response_time_ms", lambda x: np.percentile(x, 95)),
            errors=("status_code", lambda x: int(((x >= 400)).sum()))
        ).reset_index()

        grouped["avg_latency_ms"] = grouped["avg_latency_ms"].round(2)
        grouped["p95_latency_ms"] = grouped["p95_latency_ms"].round(2)
        grouped["error_rate_pct"] = (grouped["errors"] / grouped["requests"] * 100).round(2)
        return grouped.sort_values("requests", ascending=False).head(limit).reset_index(drop=True)

    @staticmethod
    def compute_top_ips(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
        """Compute most active client IP addresses."""
        if df.empty:
            return pd.DataFrame(columns=["ip_address", "requests", "percentage", "errors"])

        grouped = df.groupby("ip_address").agg(
            requests=("log_id", "count"),
            errors=("status_code", lambda x: int(((x >= 400)).sum())),
            avg_latency=("response_time_ms", "mean")
        ).reset_index()

        total = grouped["requests"].sum()
        grouped["percentage"] = (grouped["requests"] / total * 100).round(2)
        grouped["avg_latency"] = grouped["avg_latency"].round(2)
        return grouped.sort_values("requests", ascending=False).head(limit).reset_index(drop=True)


if __name__ == "__main__":
    from cassandra_manager import CassandraManager
    mgr = CassandraManager()
    ok, _ = mgr.connect()
    if ok:
        engine = AnalyticsEngine(mgr)
        dates = engine.get_available_dates()
        print("Available dates in Cassandra:", dates)
        mgr.close()

