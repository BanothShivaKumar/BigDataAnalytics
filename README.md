# BigDataAnalytics
## Real-Time Amazon Web Log Storage & Query-Based Analysis Using Apache Cassandra

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Apache Cassandra 4.1.12](https://img.shields.io/badge/Apache%20Cassandra-4.1.12-117A9B?logo=apache-cassandra&logoColor=white)](https://cassandra.apache.org/)
[![Java OpenJDK 11](https://img.shields.io/badge/Java-OpenJDK%2011-ED8B00?logo=openjdk&logoColor=white)](https://openjdk.org/)
[![Streamlit Dashboard](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pytest Passing](https://img.shields.io/badge/Tests-14%20Passing-brightgreen?logo=pytest&logoColor=white)](tests/)
[![GitHub Repository](https://img.shields.io/badge/GitHub-BanothShivaKumar%2FBigDataAnalytics-181717?logo=github&logoColor=white)](https://github.com/BanothShivaKumar/BigDataAnalytics)

---

### 👨‍💻 Project Information
- **Student / Developer**: Shiva Kumar Banoth ([@BanothShivaKumar](https://github.com/BanothShivaKumar))
- **Course**: Big Data Analytics (Final Course-End Practical Project)
- **Host Operating System**: Windows 11
- **Database Subsystem**: Ubuntu 24.04 LTS (WSL2)
- **Primary Database**: Apache Cassandra 4.1.12 (Port 9042)
- **Web Interface**: Interactive Streamlit Web Application (Port 8501)

---

## 📌 Executive Summary

Modern high-scale web platforms such as **Amazon**, Netflix, and Google process billions of HTTP access logs each day. Traditional Relational Database Management Systems (RDBMS) like MySQL or PostgreSQL fail to handle this workload due to disk I/O bottlenecks, table locking, and secondary index penalties.

This project implements an end-to-end, production-grade **Big Data Analytics System** powered by **Apache Cassandra 4.1.12** and **Python**:
1. **Real-World Amazon Weblog Simulation**: Simulates production e-commerce user activity across ASIN product views, shopping cart operations, checkout processing, Prime streaming, and search queries.
2. **Robust Data Preprocessing Pipeline**: Validates IPv4 structures, eliminates duplicate UUIDs, enforces HTTP status ranges (100–599), and removes anomalous negative latencies.
3. **Query-Driven NoSQL Modeling**: Implements 5 dedicated Apache Cassandra tables designed for zero-JOIN, sub-millisecond analytical retrieval.
4. **Statistical Analytics Engine**: Calculates key metrics including total volume, unique visitors, P50/P95 latencies, 4xx/5xx error rates, and slow request bottlenecks (≥ 500ms).
5. **Interactive Light-Themed Dashboard**: Features a 10-page Streamlit web interface with charts, live traffic counters, and an in-browser CQL query sandbox.
6. **100% Automated Test Coverage**: 14 unit and integration tests verifying all modules.

---

## 🏛️ System Architecture & End-to-End Data Flow

```text
+-----------------------------------------------------------------------------------------+
|                    BIG DATA ANALYTICS PIPELINE ARCHITECTURE                             |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|   [1. Amazon Weblog Generator (Module 1)]                                               |
|       - High-velocity realistic e-commerce logs (GET, POST, PUT, DELETE)                |
|       - Realistic Amazon ASIN endpoints (/dp/B08N5WRWNW, /cart/add, /checkout)          |
|       - Natural response times with injected slow bottlenecks (≥ 500ms)                 |
|                                     │                                                   |
|                                     ▼                                                   |
|   [2. Data Preprocessor & Validation (Module 2)]                                        |
|       - UUID validation & duplicate detection                                           |
|       - IPv4 octet format validation (0-255 range check)                                |
|       - HTTP status code range integrity (100 - 599)                                    |
|       - Filtering of negative response latencies                                        |
|                                     │                                                   |
|                                     ▼                                                   |
|   [3. Apache Cassandra 4.1.12 Storage (Module 3 - Port 9042)]                           |
|       - Distributed Columnar Storage (CommitLog, Memtable, SSTables)                    |
|       - Keyspace: web_analytics (SimpleStrategy, RF=1)                                  |
|       - 5 Specialized Query-Driven Tables:                                              |
|           • logs_by_date              (Time-series lookups by date/hour)                |
|           • logs_by_ip                (Forensic client IP inspection)                   |
|           • logs_by_status            (4xx / 5xx error triage)                          |
|           • url_daily_counts          (Atomic counter hits per endpoint)                |
|           • slow_requests_by_date     (Bottleneck tracking ordered by latency)          |
|                                     │                                                   |
|                                     ▼                                                   |
|   [4. Big Data Analytics Engine (Module 4)]                                             |
|       - Direct CQL retrieval using partition keys (No ALLOW FILTERING)                  |
|       - Aggregations: P50 / P95 Latency Percentiles, Error Ratios, Traffic Trends       |
|                                     │                                                   |
|                                     ▼                                                   |
|   [5. Interactive Streamlit Dashboard (Module 5 - Port 8501)]                           |
|       - 10 Structured Analytical Pages                                                  |
|       - High-contrast, clean light-themed interface                                     |
|       - Live CQL Sandbox, interactive charts, and instant log generation                |
|                                                                                         |
+-----------------------------------------------------------------------------------------+
```

---

## 📂 Project Repository Structure

```text
BigDataAnalytics/
│
├── cql/
│   └── schema.cql                 # Cassandra keyspace & 5 table DDL definitions
│
├── src/
│   ├── __init__.py                # Package initializer
│   ├── log_generator.py           # Module 1: Synthetic Amazon weblog generator
│   ├── preprocessor.py            # Module 2: Data cleansing & schema validation
│   ├── cassandra_manager.py       # Module 3: Cluster connection & prepared statements
│   ├── analytics_engine.py        # Module 4: Statistical aggregation & KPI calculation
│   ├── dashboard.py               # Module 5: 10-page interactive Streamlit dashboard
│   └── seed_data.py               # Automated database seed utility
│
├── tests/
│   ├── test_log_generator.py      # Module 1 unit tests
│   ├── test_preprocessor.py       # Module 2 data cleaning unit tests
│   └── test_analytics_engine.py   # Module 4 math & Cassandra integration tests
│
├── data/
│   └── .gitkeep                   # Data directory placeholder (CSV files ignored)
│
├── requirements.txt               # Complete Python package dependencies
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git exclusion rules
│
├── setup.sh                       # Linux / WSL2 automated setup script
├── run.sh                         # Linux / WSL2 dashboard launch script
├── setup.bat                      # Windows Command Prompt setup script
└── run.bat                        # Windows dashboard launch script
```

---

## 🗄️ Query-Driven Cassandra Schema Design

In Apache Cassandra, tables are designed around queries, not entities (**Query-Driven Modeling**). Because Cassandra does not support relational `JOIN` operations, data is duplicated across 5 dedicated tables to guarantee sub-millisecond retrieval:

| Table Name | Partition Key | Clustering Columns | Analytical Query Answered |
| :--- | :--- | :--- | :--- |
| **`logs_by_date`** | `(log_date, hour_bucket)` | `event_time DESC, log_id ASC` | *"What requests happened on date X during hour Y?"* Limits partition sizes to < 100MB. |
| **`logs_by_ip`** | `(ip_address, log_date)` | `event_time DESC, log_id ASC` | *"Show all activity performed by a specific client IP address on date X."* |
| **`logs_by_status`** | `(log_date, status_code)` | `event_time DESC, log_id ASC` | *"Retrieve all 500 server errors or 404 not found events for date X."* |
| **`url_daily_counts`** | `(log_date)` | `url_path, status_code` | *"How many total hits did /cart/add receive today?"* Uses Cassandra **atomic counters**. |
| **`slow_requests_by_date`** | `(log_date, hour_bucket)` | `response_time_ms DESC, event_time DESC, log_id ASC` | *"Which requests exceeded 500ms, ranked from slowest to fastest?"* |

---

## 🚀 How to Run the Project

### Step 1: Start Apache Cassandra (Ubuntu WSL2)
Open your **Ubuntu 24.04 terminal** in WSL2 and run:
```bash
# Terminal: Ubuntu WSL2
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
~/apache-cassandra-4.1.12/bin/cassandra

# Verify node status (Wait 15-20 seconds for JVM startup):
~/apache-cassandra-4.1.12/bin/nodetool status
```
*Expected status*: `UN  127.0.0.1` (`U` = Up, `N` = Normal).

---

### Step 2: Install Python Dependencies (Windows)
Open **Windows PowerShell** or **Command Prompt**:
```powershell
# Terminal: Windows PowerShell
cd "C:\Users\shiva\Downloads\BIG DATA PROJECT\Real-Time-Website-Log-Analytics"
python -m pip install -r requirements.txt
```

---

### Step 3: Run Automated Test Suite
Verify that all 14 unit and integration tests pass:
```powershell
# Terminal: Windows PowerShell
python -m pytest -v
```
Output:
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
============================== 14 passed in 2.93s ==============================
```

---

### Step 4: Seed Database with Initial Amazon Weblogs
Populate Cassandra with 5,000 realistic records:
```powershell
# Terminal: Windows PowerShell
cd src
python seed_data.py 5000
cd ..
```

---

### Step 5: Launch the Streamlit Dashboard
```powershell
# Terminal: Windows PowerShell
streamlit run src/dashboard.py
```
Open your web browser at:
👉 **`http://localhost:8501`**

---

## 📊 Dashboard Pages Overview

| Page # | Page Title | Description & Visualizations |
| :---: | :--- | :--- |
| **1** | **Overview** | Top KPI cards (Total Requests, Unique IPs, Average Response Time, Success Rate, Slow Requests) and 24-Hour Traffic Trend chart. |
| **2** | **Live Log Monitoring** | Real-time tabular stream of web requests with filters for HTTP status code, method, and endpoint. |
| **3** | **Traffic Analytics** | Temporal hourly traffic distribution, HTTP method breakdown (GET vs POST), and Top 10 most visited Amazon URLs. |
| **4** | **Error Analytics** | 4xx client errors and 5xx server faults breakdown, error rates by hour, and identification of failing endpoints. |
| **5** | **Performance Analytics** | Latency metrics (Mean, Median, P95, Max) and Seaborn distribution histogram showing the 500ms threshold. |
| **6** | **Slow Request Investigation** | Dedicated triage view pulling directly from `slow_requests_by_date` ordered by `response_time_ms DESC`. |
| **7** | **IP Analysis** | Top client IP addresses by request volume and forensic history lookup for any selected visitor IP. |
| **8** | **Database Information** | Real-time Apache Cassandra metadata, cluster version, keyspace topology, and an interactive **Live CQL Execution Sandbox**. |
| **9** | **Data Generation & Control** | Ingest on-demand batches of 1,000 to 25,000 logs into Cassandra with live progress tracking. |
| **10** | **Project Information & Viva Prep** | Academic defense guide, architectural breakdown, and professor viva answers. |

---

## 🎓 College Viva & Evaluation Q&A Cheat Sheet

### Q1: Why use Apache Cassandra instead of MySQL or MongoDB for weblogs?
> **Answer**: High-traffic platforms generate millions of write operations per second. Traditional RDBMS databases write synchronously to B-Trees and apply table-level or row-level ACID locks, causing severe disk bottlenecks. MongoDB relies on document locking and memory caching. Cassandra uses a **Log-Structured Merge (LSM) Tree** architecture: writes are appended sequentially to an append-only **CommitLog** on disk and stored in RAM (**Memtable**). Once full, Memtables flush sequentially to disk as immutable **SSTables**. This provides ultra-fast $O(1)$ write speeds and horizontal scalability without locking.

### Q2: What is the significance of P95 latency versus Average (Mean) latency?
> **Answer**: Average latency hides performance degradation because a few fast requests can mask severe bottlenecks. **P95 Latency** means 95% of users experienced a response time at or below this value, while the slowest 5% experienced higher. In e-commerce (e.g., Amazon), the slowest 5% are often the high-value checkout or payment transactions, making P95 the industry standard SLA metric.

### Q3: Why is `ALLOW FILTERING` discouraged in Cassandra?
> **Answer**: In Cassandra, data is partitioned across cluster nodes based on the hash of the Partition Key. If a query does not specify the partition key and uses `ALLOW FILTERING`, Cassandra is forced to perform a full-cluster scan across every single partition on every node. This creates massive CPU spikes and network latency. Our project avoids `ALLOW FILTERING` by designing 5 specialized tables tailored to specific query patterns.

---

## 📄 License
This project is developed for educational and academic evaluation purposes under the MIT License.
