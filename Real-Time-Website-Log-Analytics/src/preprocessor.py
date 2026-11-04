"""
Module 2: Log Preprocessing
Implements comprehensive data cleaning, validation, deduplication,
and enrichment before insertion into Apache Cassandra.
"""

import ipaddress
import re
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple, List
import pandas as pd


# Set of recognized standard HTTP methods
VALID_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


class LogPreprocessor:
    """Preprocesses raw synthetic website access logs for Apache Cassandra storage."""

    def __init__(self, slow_threshold_ms: float = 500.0):
        self.slow_threshold_ms = slow_threshold_ms
        self.metrics: Dict[str, Any] = {
            "total_records": 0,
            "duplicate_records": 0,
            "missing_values_dropped": 0,
            "invalid_records": 0,
            "valid_records": 0,
            "invalid_reasons": {},
        }

    @staticmethod
    def is_valid_ipv4(ip_str: Any) -> bool:
        """Validate if a string is a valid IPv4 address."""
        if not ip_str or not isinstance(ip_str, str):
            return False
        try:
            ipaddress.IPv4Address(ip_str.strip())
            return True
        except (ValueError, ipaddress.AddressValueError):
            return False

    @staticmethod
    def is_valid_uuid(uuid_to_test: Any) -> bool:
        """Validate if a value is a valid UUID string or UUID object."""
        if isinstance(uuid_to_test, uuid.UUID):
            return True
        if not uuid_to_test or not isinstance(uuid_to_test, str):
            return False
        try:
            uuid.UUID(str(uuid_to_test).strip())
            return True
        except (ValueError, AttributeError):
            return False

    def validate_and_clean_record(self, row: pd.Series) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate and format a single log record.

        Returns:
            (is_valid, rejection_reason, cleaned_dict)
        """
        # 1. Check for essential missing values
        required_fields = ["log_id", "timestamp", "ip_address", "http_method", "url_path", "status_code", "response_time_ms"]
        for field in required_fields:
            if field not in row or pd.isna(row[field]) or row[field] is None:
                return False, f"Missing required field: {field}", {}

        # 2. Validate and convert UUID
        raw_log_id = str(row["log_id"]).strip()
        if not self.is_valid_uuid(raw_log_id):
            return False, f"Invalid UUID: {raw_log_id}", {}
        log_id_obj = uuid.UUID(raw_log_id)

        # 3. Validate and convert Timestamp
        try:
            event_dt = pd.to_datetime(row["timestamp"])
            if pd.isna(event_dt):
                return False, "Unparseable timestamp", {}
            # Ensure Python datetime
            if hasattr(event_dt, "to_pydatetime"):
                event_dt = event_dt.to_pydatetime()
        except Exception as e:
            return False, f"Invalid timestamp format: {e}", {}

        # 4. Validate IP Address
        ip_str = str(row["ip_address"]).strip()
        if not self.is_valid_ipv4(ip_str):
            return False, f"Invalid IPv4 address: {ip_str}", {}

        # 5. Validate HTTP Method
        method = str(row["http_method"]).strip().upper()
        if method not in VALID_HTTP_METHODS:
            return False, f"Invalid HTTP method: {method}", {}

        # 6. Validate URL Path
        url_path = str(row["url_path"]).strip()
        if not url_path.startswith("/"):
            url_path = "/" + url_path

        # 7. Validate HTTP Status Code
        try:
            status_code = int(row["status_code"])
            if status_code < 100 or status_code > 599:
                return False, f"HTTP status code out of range (100-599): {status_code}", {}
        except (ValueError, TypeError):
            return False, f"Non-integer HTTP status code: {row['status_code']}", {}

        # 8. Validate Response Time
        try:
            response_time_ms = float(row["response_time_ms"])
            if response_time_ms < 0:
                return False, f"Negative response time: {response_time_ms}", {}
        except (ValueError, TypeError):
            return False, f"Non-numeric response time: {row['response_time_ms']}", {}

        # 9. Request and Response Sizes
        try:
            request_size = int(row.get("request_size", 0) or 0)
            request_size = max(0, request_size)
        except (ValueError, TypeError):
            request_size = 0

        try:
            response_size = int(row.get("response_size", 0) or 0)
            response_size = max(0, response_size)
        except (ValueError, TypeError):
            response_size = 0

        user_agent = str(row.get("user_agent", "Unknown") or "Unknown").strip()

        # Derive partition keys for Cassandra
        log_date = event_dt.date()  # Cassandra date type
        hour_bucket = event_dt.hour  # 0..23 integer bucket

        cleaned_record = {
            "log_id": log_id_obj,
            "event_time": event_dt,
            "log_date": log_date,
            "hour_bucket": hour_bucket,
            "ip_address": ip_str,
            "http_method": method,
            "url_path": url_path,
            "status_code": status_code,
            "response_time_ms": round(response_time_ms, 2),
            "user_agent": user_agent,
            "request_size_bytes": request_size,
            "response_size_bytes": response_size,
            "is_slow": response_time_ms >= self.slow_threshold_ms,
        }

        return True, "", cleaned_record

    def process(self, raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Preprocess the entire input DataFrame.

        Returns:
            (cleaned_df, preprocessing_metrics)
        """
        self.metrics = {
            "total_records": len(raw_df),
            "duplicate_records": 0,
            "missing_values_dropped": 0,
            "invalid_records": 0,
            "valid_records": 0,
            "invalid_reasons": {},
        }

        if raw_df.empty:
            return pd.DataFrame(), self.metrics

        # Step 1: Detect and drop exact duplicate records
        initial_count = len(raw_df)
        df_no_dups = raw_df.drop_duplicates(subset=["log_id"], keep="first").copy()
        duplicate_count = initial_count - len(df_no_dups)
        self.metrics["duplicate_records"] = duplicate_count

        cleaned_rows: List[Dict[str, Any]] = []

        # Step 2: Validate each record
        for _, row in df_no_dups.iterrows():
            is_valid, reason, clean_dict = self.validate_and_clean_record(row)
            if is_valid:
                cleaned_rows.append(clean_dict)
            else:
                self.metrics["invalid_records"] += 1
                self.metrics["invalid_reasons"][reason] = self.metrics["invalid_reasons"].get(reason, 0) + 1

        self.metrics["valid_records"] = len(cleaned_rows)
        cleaned_df = pd.DataFrame(cleaned_rows)
        return cleaned_df, self.metrics


if __name__ == "__main__":
    from log_generator import generate_logs
    print("Testing Preprocessor with synthetic anomalies...")
    raw = generate_logs(num_records=1000, include_anomalies=True)
    processor = LogPreprocessor()
    clean_df, summary = processor.process(raw)
    print(f"Total: {summary['total_records']}, Duplicates: {summary['duplicate_records']}, "
          f"Invalid: {summary['invalid_records']}, Valid: {summary['valid_records']}")
    print("Invalid reasons breakdown:", summary["invalid_reasons"])

