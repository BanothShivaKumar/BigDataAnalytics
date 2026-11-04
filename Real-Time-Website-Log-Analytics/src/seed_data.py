"""
Seed Script: Generates 5,000 synthetic website access logs, preprocesses them,
and populates all 5 Apache Cassandra tables.
"""

import os
import sys

# Ensure src is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from log_generator import generate_logs, save_logs_to_csv
from preprocessor import LogPreprocessor
from cassandra_manager import CassandraManager


def seed_database(num_records: int = 5000, days_back: int = 2):
    print(f"============================================================")
    print(f"  Step 1: Generating {num_records:,} Synthetic Website Logs")
    print(f"============================================================")
    raw_df = generate_logs(num_records=num_records, days_back=days_back, include_anomalies=True, seed=42)

    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "website_logs.csv")
    save_logs_to_csv(raw_df, csv_path)
    print(f"Saved {len(raw_df):,} raw logs to {csv_path}")

    print(f"\n============================================================")
    print(f"  Step 2: Preprocessing & Data Cleaning (Module 2)")
    print(f"============================================================")
    preprocessor = LogPreprocessor()
    clean_df, summary = preprocessor.process(raw_df)
    print(f"  - Total Raw Records:       {summary['total_records']:,}")
    print(f"  - Duplicate Records Dropped: {summary['duplicate_records']:,}")
    print(f"  - Invalid Records Filtered: {summary['invalid_records']:,}")
    print(f"  - Valid Cleaned Records:   {summary['valid_records']:,}")

    print(f"\n============================================================")
    print(f"  Step 3: Connecting to Apache Cassandra & Ingesting")
    print(f"============================================================")
    mgr = CassandraManager()
    ok, msg = mgr.connect()
    if not ok:
        print(f"ERROR: Could not connect to Cassandra: {msg}")
        return False

    print("Connected to Cassandra. Writing records across all 5 tables...")
    last_pct = 0

    def progress_callback(curr, total):
        nonlocal last_pct
        pct = int((curr / total) * 100)
        if pct >= last_pct + 20 or curr == total:
            last_pct = pct
            print(f"  Progress: {curr:,}/{total:,} records ({pct}%)")

    result = mgr.insert_batch(clean_df, progress_callback=progress_callback)
    print(f"\nSuccessfully stored {result['success']:,} records in Cassandra!")
    if result["failure"] > 0:
        print(f"Insertion failures: {result['failure']:,}")

    mgr.close()
    print("Database connection closed cleanly.")
    return True


if __name__ == "__main__":
    count = 5000
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
    seed_database(num_records=count)

