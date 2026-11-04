"""
Unit tests for Module 2: Log Preprocessing
"""

import sys
import os
import uuid
from datetime import datetime
import pandas as pd
import pytest

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from preprocessor import LogPreprocessor


@pytest.fixture
def preprocessor():
    return LogPreprocessor(slow_threshold_ms=500.0)


def test_ipv4_validation(preprocessor):
    """Test IPv4 format validation helper."""
    assert preprocessor.is_valid_ipv4("192.168.1.1") is True
    assert preprocessor.is_valid_ipv4("10.0.0.254") is True
    assert preprocessor.is_valid_ipv4("999.999.999.999") is False
    assert preprocessor.is_valid_ipv4("invalid-ip-string") is False
    assert preprocessor.is_valid_ipv4(None) is False


def test_uuid_validation(preprocessor):
    """Test UUID format validation helper."""
    valid_id = str(uuid.uuid4())
    assert preprocessor.is_valid_uuid(valid_id) is True
    assert preprocessor.is_valid_uuid(uuid.uuid4()) is True
    assert preprocessor.is_valid_uuid("not-a-valid-uuid") is False
    assert preprocessor.is_valid_uuid("") is False


def test_missing_values_detection(preprocessor):
    """Verify that records with missing essential fields are rejected."""
    bad_record = pd.Series({
        "log_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "ip_address": None,  # Missing IP
        "http_method": "GET",
        "url_path": "/api",
        "status_code": 200,
        "response_time_ms": 100.0,
    })
    is_valid, reason, _ = preprocessor.validate_and_clean_record(bad_record)
    assert is_valid is False
    assert "Missing required field" in reason


def test_status_code_validation(preprocessor):
    """Verify HTTP status codes out of range 100-599 are rejected."""
    bad_record = pd.Series({
        "log_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "ip_address": "192.168.1.1",
        "http_method": "GET",
        "url_path": "/api",
        "status_code": 999,  # Out of range
        "response_time_ms": 100.0,
    })
    is_valid, reason, _ = preprocessor.validate_and_clean_record(bad_record)
    assert is_valid is False
    assert "status code out of range" in reason


def test_negative_response_time_validation(preprocessor):
    """Verify negative latencies are rejected."""
    bad_record = pd.Series({
        "log_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "ip_address": "192.168.1.1",
        "http_method": "GET",
        "url_path": "/api",
        "status_code": 200,
        "response_time_ms": -45.0,  # Negative
    })
    is_valid, reason, _ = preprocessor.validate_and_clean_record(bad_record)
    assert is_valid is False
    assert "Negative response time" in reason


def test_duplicate_detection(preprocessor):
    """Verify duplicate records are detected and dropped."""
    same_id = str(uuid.uuid4())
    rows = [
        {
            "log_id": same_id,
            "timestamp": datetime.now().isoformat(),
            "ip_address": "192.168.1.10",
            "http_method": "GET",
            "url_path": "/home",
            "status_code": 200,
            "response_time_ms": 80.0,
        },
        {
            "log_id": same_id,  # Duplicate ID
            "timestamp": datetime.now().isoformat(),
            "ip_address": "192.168.1.10",
            "http_method": "GET",
            "url_path": "/home",
            "status_code": 200,
            "response_time_ms": 80.0,
        }
    ]
    raw_df = pd.DataFrame(rows)
    clean_df, summary = preprocessor.process(raw_df)
    assert summary["duplicate_records"] == 1
    assert summary["valid_records"] == 1
    assert len(clean_df) == 1

