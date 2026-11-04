# Real-Time Website Log Storage and Query-Based Analysis Using Apache Cassandra

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Apache Cassandra](https://img.shields.io/badge/Apache%20Cassandra-4.1.12-117A9B.svg)](https://cassandra.apache.org/)
[![Java](https://img.shields.io/badge/Java-OpenJDK%2011-orange.svg)](https://openjdk.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-14%20Passing-brightgreen.svg)](tests/)

A complete, production-grade Big Data Analytics course-end academic project. The system simulates high-velocity website access logs, preprocesses and validates records, ingests them into a distributed **Apache Cassandra 4.1.12** NoSQL database across query-driven tables, runs statistical analytical aggregations, and provides a 10-page interactive **Streamlit** dashboard.

---

## 1. Project Introduction

High-traffic websites (e.g., e-commerce platforms, streaming services, social media) generate millions of HTTP access logs every hour. Traditional relational databases (RDBMS) like MySQL or PostgreSQL struggle under sustained write loads due to ACID locking, indexing overhead, and disk I/O bottlenecks. 

This project demonstrates how **Apache Cassandra**, a distributed NoSQL columnar database built on the Google Bigtable and Amazon Dynamo papers, provides:
- **Massive write throughput** via Log-Structured Merge (LSM) Trees, CommitLogs, and Memtables.
- **Query-driven data modeling** without expensive SQL `JOIN` operations.
- **Linear horizontal scalability** with zero single points of failure.
- **Sub-millisecond query performance** for time-series log analysis.

---

## 2. Project Objectives

1. **Synthetic Data Generation**: Produce realistic web traffic logs with configurable volume (5,000 to 25,000+ records) covering HTTP methods, URLs, status codes, user agents, and normal vs. slow response times.
2. **Data Preprocessing & Validation**: Clean incoming data, drop duplicate UUIDs, validate IPv4 formats, check HTTP status codes (100–599), and filter negative latencies.
3. **NoSQL Database Management**: Automatically provision keyspace `web_analytics` and 5 specialized Cassandra tables using prepared statements and atomic counters.
4. **Query-Based Analytics**: Calculate key performance indicators (KPIs) including total traffic, unique visitors, P50/P95 latencies, error distributions (4xx/5xx), and slow request bottlenecks (≥ 500ms).
5. **Interactive 10-Page Dashboard**: Build a modern, responsive Streamlit dashboard suitable for live demonstrations and academic evaluations.
6. **Automated Unit & Integration Testing**: Ensure 100% test coverage for log generation, data cleaning, statistical math, and Cassandra connectivity.

---

## 3. Technology Stack

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Database** | Apache Cassandra | 4.1.12 | Distributed NoSQL storage for time-series logs |
| **Runtime / JVM** | OpenJDK | 11 | Required runtime for Apache Cassandra 4.1 |
| **Language** | Python | 3.10 – 3.13 | Backend logic, ETL pipeline, and analytics |
| **Driver** | DataStax Cassandra Driver | 3.29+ / 3.30+ | Binary protocol CQL connection to port 9042 |
| **Data Processing** | Pandas & NumPy | 2.1+ / 1.26+ | In-memory dataframes and percentile calculations |
| **Visualization** | Matplotlib & Seaborn | 3.8+ / 0.13+ | Statistical histograms and latency distributions |
| **User Interface** | Streamlit | 1.30+ | 10-page interactive analytical web dashboard |
| **Testing** | Pytest | 7.4+ | Automated unit and integration test suite |

---

## 4. System Architecture & Data Flow

```text
+---------------------------------------------------------------------------------+
|                               SYSTEM DATA FLOW                                  |
+---------------------------------------------------------------------------------+
|                                                                                 |
|   [1. Log Generator (Module 1)]                                                 |
|       Generates synthetic web traffic (methods, paths, latencies, IPs)          |
|                         |                                                       |
|                         v                                                       |
|   [2. Data Preprocessor (Module 2)]                                             |
|       Deduplication, UUID validation, IP format checks, status range checks     |
|                         |                                                       |
|                         v                                                       |
|   [3. Apache Cassandra (Module 3 - Port 9042)]                                  |
|       NoSQL Distributed Columnar Storage (LSM-Tree, CommitLog, SSTables)        |
|       5 Tables: logs_by_date, logs_by_ip, logs_by_status,                       |
|                 url_daily_counts, slow_requests_by_date                         |
|                         |                                                       |
|                         v                                                       |
|   [4. Analytics Engine (Module 4)]                                              |
|       Query-driven CQL retrieval, P95 latency percentiles, error rate math      |
|                         |                                                       |
|                         v                                                       |
|   [5. Streamlit Dashboard (Module 5)]                                           |
|       10 Interactive analytical views with charts, KPIs, and controls           |
|                                                                                 |
+---------------------------------------------------------------------------------+
```

---

## 5. Folder Structure

```text
Real-Time-Website-Log-Analytics/
│
├── cql/
│   └── schema.cql                 # Cassandra Keyspace and 5 Table schemas
│
├── src/
│   ├── __init__.py                # Package initialization
│   ├── log_generator.py           # Module 1: Synthetic log generation
│   ├── preprocessor.py            # Module 2: Data cleaning & validation
│   ├── cassandra_manager.py       # Module 3: Cluster connection & prepared statements
│   ├── analytics_engine.py        # Module 4: Statistical and analytical aggregations
│   ├── dashboard.py               # Module 5: 10-page interactive Streamlit UI
│   └── seed_data.py               # CLI utility to generate & seed baseline data
│
├── tests/
│   ├── test_log_generator.py      # Module 1 unit tests
│   ├── test_preprocessor.py       # Module 2 data cleaning unit tests
│   └── test_analytics_engine.py   # Module 4 math & Cassandra integration tests
│
├── data/
│   ├── .gitkeep                   # Directory placeholder
│   └── website_logs.csv           # Stored generated synthetic log CSV
│
├── requirements.txt               # Python package dependencies
├── .env.example                   # Environment variable template
├── .gitignore                     # Git exclusion rules
│
├── setup.sh                       # Linux / WSL2 automated setup script
├── run.sh                         # Linux / WSL2 dashboard launch script
├── setup.bat                      # Windows Command Prompt setup script
└── run.bat                        # Windows dashboard launch script
```

---

## 6. Why 5 Apache Cassandra Tables?

In Apache Cassandra, data modeling follows a **Query-Driven Design Rule**:  
> *"Model your tables around your queries, not around your entities."*

Cassandra does not support relational `JOIN` operations, and querying with `ALLOW FILTERING` triggers costly cluster-wide partition scans. To provide sub-millisecond query response times for the dashboard, 5 specialized tables are used:

| Table Name | Partition Key | Clustering Columns | Analytical Purpose |
| :--- | :--- | :--- | :--- |
| **`logs_by_date`** | `(log_date, hour_bucket)` | `event_time DESC, log_id ASC` | Primary time-series log lookups. Partitioning by date and hour prevents partitions from exceeding Cassandra's recommended 100MB size limit. |
| **`logs_by_ip`** | `(ip_address, log_date)` | `event_time DESC, log_id ASC` | Instant forensic lookups of all requests made by a specific IP on a given day. |
| **`logs_by_status`** | `(log_date, status_code)` | `event_time DESC, log_id ASC` | Fast triage of specific HTTP error codes (e.g., retrieving only 500 Internal Server Errors or 404 Not Founds). |
| **`url_daily_counts`** | `(log_date)` | `url_path, status_code` | Aggregated endpoint hits per day. Uses Cassandra's native **atomic counter columns** (`request_count counter`). |
| **`slow_requests_by_date`** | `(log_date, hour_bucket)` | `response_time_ms DESC, event_time DESC, log_id ASC` | Stores requests exceeding the 500ms threshold. Clustering by `response_time_ms DESC` ensures the slowest requests appear at the top. |

---

## 7. Step-by-Step Installation & Setup

### Environment Prerequisites
- **Host OS**: Windows 11
- **Linux Subsystem**: Ubuntu 24.04 LTS via WSL2
- **Java**: OpenJDK 11 (`/usr/lib/jvm/java-11-openjdk-amd64`)
- **Cassandra**: Apache Cassandra 4.1.12
- **Python**: Python 3.10+ (tested on Python 3.13)

---

### Step 7.1: Verify Java 11 in Ubuntu WSL2
Inside your Ubuntu terminal, verify OpenJDK 11:
```bash
# Terminal: Ubuntu WSL2
/usr/lib/jvm/java-11-openjdk-amd64/bin/java -version
```
Expected output:
```text
openjdk version "11.0.32.1"
```

---

### Step 7.2: Download & Extract Apache Cassandra 4.1.12 (WSL2)
If not already downloaded, extract Apache Cassandra 4.1.12 to your home directory:
```bash
# Terminal: Ubuntu WSL2
cd ~
curl -fSL https://dlcdn.apache.org/cassandra/4.1.12/apache-cassandra-4.1.12-bin.tar.gz -o cassandra-4.1.12.tar.gz
tar -xzf cassandra-4.1.12.tar.gz
```

---

### Step 7.3: Start Apache Cassandra in WSL2
Launch Cassandra as a background daemon:
```bash
# Terminal: Ubuntu WSL2
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
~/apache-cassandra-4.1.12/bin/cassandra
```
Verify that Cassandra has joined the ring (status `UN` = Up/Normal):
```bash
# Terminal: Ubuntu WSL2
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
~/apache-cassandra-4.1.12/bin/nodetool status
```
Expected output:
```text
Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address    Load        Tokens  Owns (effective)  Host ID                               Rack
UN  127.0.0.1  120.37 KiB  16      100.0%            40f96e13-15d0-4b9d-a714-4c1d8e11d2ea  rack1
```

> **Note**: WSL2 automatically mirrors `localhost:9042` to your Windows host. Python running on Windows can connect directly to `127.0.0.1:9042`.

---

### Step 7.4: Python Setup (Windows or WSL2)

#### Option A: Running from Windows (PowerShell or Command Prompt)
```powershell
# Terminal: Windows PowerShell
cd "C:\Users\shiva\Downloads\BIG DATA PROJECT\Real-Time-Website-Log-Analytics"
python -m pip install -r requirements.txt
```

#### Option B: Running from Ubuntu WSL2
```bash
# Terminal: Ubuntu WSL2
cd "/mnt/c/Users/shiva/Downloads/BIG DATA PROJECT/Real-Time-Website-Log-Analytics"
bash setup.sh
```

---

## 8. Seeding Sample Data & Running the Application

### Step 8.1: Seed 5,000 Sample Records
To populate Cassandra with the initial 5,000 synthetic website logs:
```powershell
# Terminal: Windows PowerShell
cd "C:\Users\shiva\Downloads\BIG DATA PROJECT\Real-Time-Website-Log-Analytics\src"
python seed_data.py 5000
```
This script:
1. Generates 5,000 realistic logs spanning the last 2 days.
2. Injects synthetic anomalies (duplicates, invalid IPs, status codes).
3. Executes Module 2 cleaning and logs valid vs. dropped counts.
4. Concurrently writes to all 5 Cassandra tables using prepared statements.

---

### Step 8.2: Launch the Streamlit Dashboard
```powershell
# Terminal: Windows PowerShell
cd "C:\Users\shiva\Downloads\BIG DATA PROJECT\Real-Time-Website-Log-Analytics"
streamlit run src/dashboard.py
```
Open your web browser and navigate to:
```text
http://localhost:8501
```

---

## 9. Dashboard Pages Guide

The dashboard is organized into 10 structured pages:

1. **1. Overview**: High-level executive KPI cards (Total Requests, Unique IPs, Average Response Time, Success Rate, Slow Requests) with Hourly Traffic trend and HTTP Status Distribution charts.
2. **2. Live Log Monitoring**: Live stream table displaying incoming requests (Timestamp, Method, Status, Latency, URL, IP). Includes search filters and auto-refresh controls.
3. **3. Traffic Analytics**: Detailed temporal traffic analysis featuring a 24-hour bar chart, HTTP method distribution, and top requested URL endpoints.
4. **4. Error Analytics**: In-depth triage of 4xx client errors and 5xx server failures, error frequency bar charts, and ranking of the most problematic endpoints.
5. **5. Performance Analytics**: Latency statistics (Mean, Median, P95, Max) and a Seaborn-rendered latency distribution histogram with a 500ms slow threshold indicator.
6. **6. Slow Request Investigation**: Dedicated query view against `slow_requests_by_date` displaying requests ordered by `response_time_ms DESC`.
7. **7. IP Analysis**: Client IP address frequency table and an interactive dropdown allowing forensic log inspection for any selected IP.
8. **8. Database Information**: Live Cassandra cluster metadata (Cluster Name, Release Version, Keyspace, Host ID) and an interactive **CQL Execution Sandbox**.
9. **9. Data Generation & Control**: Interactive control panel to generate additional batches of logs (1,000 to 25,000), run preprocessing, and monitor insertion with a real-time progress bar.
10. **10. Project Information & Viva Prep**: Comprehensive academic defense guide covering system architecture, Big Data principles, Cassandra trade-offs, and typical professor examination questions.

---

## 10. Automated Testing

Run the automated test suite with pytest:
```powershell
# Terminal: Windows PowerShell
cd "C:\Users\shiva\Downloads\BIG DATA PROJECT\Real-Time-Website-Log-Analytics"
python -m pytest -v
```

All 14 automated unit and integration tests pass:
```text
tests/test_analytics_engine.py::test_compute_overview_metrics PASSED      [  7%]
tests/test_analytics_engine.py::test_hourly_traffic_aggregation PASSED    [ 14%]
tests/test_analytics_engine.py::test_top_endpoints_aggregation PASSED     [ 21%]
tests/test_analytics_engine.py::test_cassandra_live_integration PASSED    [ 28%]
tests/test_log_generator.py::test_single_log_structure PASSED             [ 35%]
tests/test_log_generator.py::test_generate_logs_volume PASSED             [ 42%]
tests/test_log_generator.py::test_generate_logs_chronological_order PASSED  [ 50%]
tests/test_log_generator.py::test_force_slow_request PASSED               [ 57%]
tests/test_preprocessor.py::test_ipv4_validation PASSED                   [ 64%]
tests/test_preprocessor.py::test_uuid_validation PASSED                   [ 71%]
tests/test_preprocessor.py::test_missing_values_detection PASSED          [ 78%]
tests/test_preprocessor.py::test_status_code_validation PASSED            [ 85%]
tests/test_preprocessor.py::test_negative_response_time_validation PASSED  [ 92%]
tests/test_preprocessor.py::test_duplicate_detection PASSED               [100%]
============================== 14 passed in 9.43s ==============================
```

---

## 11. Common Errors and Solutions

### 1. `nodetool: Failed to connect to '127.0.0.1:7199' - Connection refused`
- **Cause**: Cassandra is still initializing the JVM or is not running.
- **Solution**: Cassandra takes 15–25 seconds to start. Wait 20 seconds, or check logs with: `tail -n 30 ~/apache-cassandra-4.1.12/logs/system.log`.

### 2. `Unable to import asyncore module` (Python 3.12+)
- **Cause**: Python 3.12 removed the legacy `asyncore` module from standard library.
- **Solution**: Install `pyasyncore` (`pip install pyasyncore`). The project's `cassandra_manager.py` automatically injects this polyfill.

### 3. Port 9042 Connection Refused from Windows
- **Cause**: Cassandra is not started in WSL2, or is bound to a non-loopback IP.
- **Solution**: Confirm Cassandra is running in Ubuntu WSL (`ps aux | grep cassandra`). WSL2 mirrors `127.0.0.1` to Windows automatically.

---

## 12. College Project Demonstration Script (Viva Walkthrough)

When presenting this project to your professor or evaluator:

1. **Step 1: Show Cassandra Running in WSL2**
   - Open your Ubuntu terminal.
   - Run: `~/apache-cassandra-4.1.12/bin/nodetool status`
   - Point out `UN 127.0.0.1` and explain: *"Cassandra is running as a single-node cluster with status Up/Normal on port 9042."*

2. **Step 2: Show the Automated Test Suite**
   - Run: `python -m pytest -v`
   - Point out that all 14 tests pass, including data validation, latency percentiles, and live Cassandra integration.

3. **Step 3: Open the Streamlit Dashboard**
   - Run: `streamlit run src/dashboard.py`
   - Show **Page 1 (Overview)**: Explain the KPIs (Total Requests, Success Rate, Average Latency, P95).
   - Show **Page 5 (Performance Analytics)**: Explain the difference between Median (P50) and P95 latency.
   - Show **Page 6 (Slow Request Investigation)**: Explain how Cassandra's clustering key `response_time_ms DESC` retrieves slow bottlenecks without sorting in Python memory.
   - Show **Page 8 (Database Information)**: Execute a live CQL query in the interactive sandbox (e.g. `SELECT * FROM url_daily_counts LIMIT 5`).
   - Show **Page 9 (Data Generation & Control)**: Generate an additional 1,000 records on the spot to demonstrate the real-time ingestion pipeline.

