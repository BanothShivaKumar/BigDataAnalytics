-- ============================================================================
-- Apache Cassandra Database Schema
-- Project: Real-Time Website Log Storage and Query-Based Analysis
-- Target Cassandra: 4.1.x
-- Replication: SimpleStrategy, replication_factor = 1 (Single Node Development)
-- ============================================================================

-- Step 1: Create Keyspace
CREATE KEYSPACE IF NOT EXISTS web_analytics
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE web_analytics;

-- ============================================================================
-- Table 1: logs_by_date
-- Purpose: Primary time-series log storage partitioned by date and hour bucket.
-- Supports efficient time-range log queries without unbounded partition growth.
-- Partition key: (log_date, hour_bucket)
-- Clustering columns: event_time DESC, log_id ASC
-- ============================================================================
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

-- ============================================================================
-- Table 2: logs_by_ip
-- Purpose: Supports IP forensic analysis and traffic inspection by client IP.
-- Partition key: (ip_address, log_date)
-- Clustering columns: event_time DESC, log_id ASC
-- ============================================================================
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

-- ============================================================================
-- Table 3: logs_by_status
-- Purpose: Fast error triage (4xx, 5xx) and status-specific traffic queries.
-- Partition key: (log_date, status_code)
-- Clustering columns: event_time DESC, log_id ASC
-- ============================================================================
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

-- ============================================================================
-- Table 4: url_daily_counts
-- Purpose: Aggregated request counts per URL endpoint and HTTP status per day.
-- Uses native Cassandra COUNTER columns with atomic increment semantics.
-- Partition key: log_date
-- Clustering columns: url_path, status_code
-- ============================================================================
CREATE TABLE IF NOT EXISTS url_daily_counts (
    log_date date,
    url_path text,
    status_code int,
    request_count counter,
    PRIMARY KEY ((log_date), url_path, status_code)
);

-- ============================================================================
-- Table 5: slow_requests_by_date
-- Purpose: Dedicated query-driven table for latency investigation (>= 500 ms).
-- Clustering order puts slowest requests at the very top for instant lookup.
-- Partition key: (log_date, hour_bucket)
-- Clustering columns: response_time_ms DESC, event_time DESC, log_id ASC
-- ============================================================================
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

