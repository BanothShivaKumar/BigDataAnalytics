"""
Unit tests for Module 1: Website Log Generator
"""

import sys
import os
import pytest
import pandas as pd

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from log_generator import generate_single_log, generate_logs, HTTP_METHODS, URL_PATHS, STATUS_CODES
from datetime import datetime


def test_single_log_structure():
    """Verify that a single generated log contains all required fields."""
    record = generate_single_log(datetime.now())

    required_keys = [
        "log_id", "timestamp", "ip_address", "http_method",
        "url_path", "status_code", "response_time_ms",
        "user_agent", "request_size", "response_size"
    ]
    for key in required_keys:
        assert key in record, f"Missing required key: {key}"

    assert record["http_method"] in HTTP_METHODS
    assert record["url_path"].startswith("/")
    assert record["status_code"] in STATUS_CODES
    assert record["response_time_ms"] > 0
    assert record["request_size"] >= 0
    assert record["response_size"] >= 0


def test_generate_logs_volume():
    """Verify configurable volume generation."""
    count = 200
    df = generate_logs(num_records=count, days_back=1, include_anomalies=False, seed=123)
    assert len(df) == count
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_generate_logs_chronological_order():
    """Verify generated records are chronologically ordered."""
    df = generate_logs(num_records=100, days_back=2, include_anomalies=False, seed=42)
    timestamps = pd.to_datetime(df["timestamp"])
    assert (timestamps.diff().dropna() >= pd.Timedelta(0)).all()


def test_force_slow_request():
    """Verify that force_slow produces latency >= 500 ms."""
    for _ in range(20):
        rec = generate_single_log(datetime.now(), force_slow=True)
        assert rec["response_time_ms"] >= 500.0

