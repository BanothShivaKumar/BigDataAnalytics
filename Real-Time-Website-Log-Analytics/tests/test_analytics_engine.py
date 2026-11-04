"""
Unit and Integration tests for Module 4: Analytics Engine
"""

import sys
import os
import uuid
from datetime import datetime, date
import pandas as pd
import numpy as np
import pytest

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from analytics_engine import AnalyticsEngine
from cassandra_manager import CassandraManager


class DummyDbManager:
    """Mock DB manager for pure unit testing without Cassandra."""
    def __init__(self):
        self.is_connected = False


@pytest.fixture
def sample_log_df():
    """Create a deterministic synthetic dataset for statistical validation."""
    data = [
        {"log_id": str(uuid.uuid4()), "ip_address": "192.168.1.1", "http_method": "GET", "url_path": "/home", "status_code": 200, "response_time_ms": 100.0, "hour_bucket": 10},
        {"log_id": str(uuid.uuid4()), "ip_address": "192.168.1.1", "http_method": "GET", "url_path": "/home", "status_code": 200, "response_time_ms": 150.0, "hour_bucket": 10},
        {"log_id": str(uuid.uuid4()), "ip_address": "192.168.1.2", "http_method": "POST", "url_path": "/login", "status_code": 401, "response_time_ms": 200.0, "hour_bucket": 11},
        {"log_id": str(uuid.uuid4()), "ip_address": "192.168.1.3", "http_method": "GET", "url_path": "/api/data", "status_code": 500, "response_time_ms": 600.0, "hour_bucket": 11}, # Slow
        {"log_id": str(uuid.uuid4()), "ip_address": "192.168.1.4", "http_method": "GET", "url_path": "/search", "status_code": 200, "response_time_ms": 800.0, "hour_bucket": 12}, # Slow
    ]
    df = pd.DataFrame(data)
    df["event_time"] = datetime.now()
    return df


def test_compute_overview_metrics(sample_log_df):
    """Test response time calculations, percentiles, and success rates."""
    engine = AnalyticsEngine(DummyDbManager(), slow_threshold_ms=500.0)
    metrics = engine.compute_overview_metrics(sample_log_df)

    assert metrics["total_requests"] == 5
    assert metrics["unique_ips"] == 4
    # Latencies: [100, 150, 200, 600, 800] -> mean = 370.0
    assert metrics["avg_response_time"] == 370.0
    assert metrics["min_response_time"] == 100.0
    assert metrics["max_response_time"] == 800.0
    assert metrics["median_response_time"] == 200.0

    # Slow requests (>= 500ms): 600, 800 -> 2
    assert metrics["slow_requests_count"] == 2
    assert metrics["slow_requests_pct"] == 40.0

    # Success (200): 3 -> 60%
    assert metrics["success_count"] == 3
    assert metrics["success_rate"] == 60.0

    # Errors: 1 client (401), 1 server (500) -> 2 errors = 40%
    assert metrics["client_errors_count"] == 1
    assert metrics["server_errors_count"] == 1
    assert metrics["error_rate"] == 40.0


def test_hourly_traffic_aggregation(sample_log_df):
    """Test hourly traffic volume aggregation."""
    engine = AnalyticsEngine(DummyDbManager())
    hourly = engine.compute_hourly_traffic(sample_log_df)

    assert len(hourly) == 24
    hour_10 = hourly.loc[hourly["hour"] == 10, "request_count"].values[0]
    hour_11 = hourly.loc[hourly["hour"] == 11, "request_count"].values[0]
    hour_12 = hourly.loc[hourly["hour"] == 12, "request_count"].values[0]
    hour_0 = hourly.loc[hourly["hour"] == 0, "request_count"].values[0]

    assert hour_10 == 2
    assert hour_11 == 2
    assert hour_12 == 1
    assert hour_0 == 0


def test_top_endpoints_aggregation(sample_log_df):
    """Test URL endpoint request counts and error rates."""
    engine = AnalyticsEngine(DummyDbManager())
    top_urls = engine.compute_top_endpoints(sample_log_df)

    assert len(top_urls) == 4
    # /home had 2 requests, 0 errors
    home_row = top_urls[top_urls["url_path"] == "/home"].iloc[0]
    assert home_row["requests"] == 2
    assert home_row["errors"] == 0

    # /api/data had 1 request, 1 error
    api_row = top_urls[top_urls["url_path"] == "/api/data"].iloc[0]
    assert api_row["requests"] == 1
    assert api_row["errors"] == 1


# -----------------------------------------------------------------------------
# Optional Integration Test (runs if local Cassandra is active)
# -----------------------------------------------------------------------------
def test_cassandra_live_integration():
    """Verify live Cassandra connectivity and keyspace/table creation."""
    mgr = CassandraManager()
    ok, msg = mgr.connect()
    if not ok:
        pytest.skip(f"Cassandra not reachable on 127.0.0.1:9042 - skipping live integration test.")

    try:
        info = mgr.get_cluster_info()
        assert info["connected"] is True
        assert "web_analytics" in info["keyspace"]
        assert len(info["tables"]) == 5
        assert "logs_by_date" in info["tables"]
        assert "logs_by_ip" in info["tables"]
        assert "logs_by_status" in info["tables"]
        assert "url_daily_counts" in info["tables"]
        assert "slow_requests_by_date" in info["tables"]
    finally:
        mgr.close()

