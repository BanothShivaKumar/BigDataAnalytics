"""
Module 5: Real-World Amazon E-Commerce Weblog Analytics Dashboard
A completely redesigned, light-themed, high-contrast Big Data Analytics platform
powered by Apache Cassandra 4.1 and Streamlit.
"""

import os
import sys
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure local src directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cassandra_manager import CassandraManager
from analytics_engine import AnalyticsEngine
from log_generator import generate_logs, save_logs_to_csv
from preprocessor import LogPreprocessor


# Page Configuration
st.set_page_config(
    page_title="Amazon Weblog Analytics | Apache Cassandra",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Premium Light-Themed CSS (High Contrast, Crisp Typography, Zero Dark Elements)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global Background and Typography */
    .stApp {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }

    /* Top Brand Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #FFFFFF 0%, #EFF6FF 100%);
        border: 1px solid #BFDBFE;
        border-radius: 12px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.05);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #1E3A8A;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #334155;
        margin-top: 8px;
        font-weight: 450;
    }

    /* Badges */
    .badge-aws {
        display: inline-block;
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FCD34D;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-cassandra {
        display: inline-block;
        background-color: #E0E7FF;
        color: #3730A3;
        border: 1px solid #C7D2FE;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-left: 8px;
    }
    .badge-live {
        display: inline-block;
        background-color: #D1FAE5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-left: 8px;
    }

    /* Custom Metric Tiles */
    .metric-container {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 18px 20px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
        border-left: 4px solid #2563EB;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
    }
    .metric-label {
        font-size: 0.86rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .metric-value {
        font-size: 1.95rem;
        font-weight: 800;
        color: #0F172A;
        margin-top: 4px;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.82rem;
        color: #475569;
        margin-top: 4px;
    }

    /* Streamlit Native Overrides for Total Legibility */
    div[data-testid="stMetricValue"] {
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
    }

    /* Section Cards */
    .section-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #1E3A8A !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Database Manager in Streamlit session state
@st.cache_resource
def get_cassandra_manager():
    mgr = CassandraManager()
    ok, msg = mgr.connect()
    return mgr, ok, msg


def load_data_for_date(engine: AnalyticsEngine, target_date: date) -> pd.DataFrame:
    """Cached loader for log data to optimize dashboard responsiveness."""
    return engine.fetch_logs_for_date(target_date)


def main():
    mgr, conn_ok, conn_msg = get_cassandra_manager()
    engine = AnalyticsEngine(mgr)

    # -------------------------------------------------------------------------
    # Sidebar Navigation
    # -------------------------------------------------------------------------
    st.sidebar.markdown("""
        <div style="padding: 10px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 20px;">
            <div style="font-size: 1.3rem; font-weight: 800; color: #1E3A8A; display: flex; align-items: center; gap: 8px;">
                <span>📦</span> Amazon Analytics
            </div>
            <div style="font-size: 0.82rem; color: #64748B; font-weight: 500; margin-top: 3px;">Real-Time Weblog Analysis</div>
        </div>
    """, unsafe_allow_html=True)

    pages = [
        "1. Executive Overview",
        "2. Live Amazon Stream",
        "3. Traffic & Workload",
        "4. Error Triage & Failures",
        "5. Latency & P95 Profiling",
        "6. Slow Request Investigation",
        "7. Shopper IP Forensics",
        "8. Cassandra Schema & CQL",
        "9. Data Pipeline & Ingestion",
        "10. Project Defense & Viva Guide",
    ]

    selected_page = st.sidebar.radio("Navigation Menu", pages)

    # Global Date Filter
    selected_date = date.today()
    if conn_ok:
        available_dates = engine.get_available_dates()
        if available_dates:
            st.sidebar.markdown("<br>", unsafe_allow_html=True)
            st.sidebar.markdown("<div style='font-size: 0.82rem; font-weight: 700; color: #475569; text-transform: uppercase; margin-bottom: 6px;'>Analysis Date</div>", unsafe_allow_html=True)
            selected_date = st.sidebar.selectbox("Select Log Date", available_dates, index=0, label_visibility="collapsed")
        else:
            selected_date = date.today()

    # -------------------------------------------------------------------------
    # PAGE 1: EXECUTIVE OVERVIEW
    # -------------------------------------------------------------------------
    if selected_page == "1. Executive Overview":
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">
                <span>📦</span> Amazon E-Commerce Weblog Analytics
            </div>
            <div class="hero-subtitle">
                Real-time query-driven performance monitoring and operational telemetry powered by Apache Cassandra.
            </div>
            <div style="margin-top: 14px;">
                <span class="badge-aws">Amazon Production Telemetry</span>
                <span class="badge-cassandra">Distributed Query Engine</span>
                <span class="badge-live">Real-Time Ingestion</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not conn_ok:
            st.warning("⚠️ Apache Cassandra is currently offline. Please verify that Cassandra is running in your WSL2 terminal.")
            return

        df = load_data_for_date(engine, selected_date)
        if df.empty:
            st.info("ℹ️ No log records found in Cassandra for the selected date. Navigate to **9. Data Pipeline & Ingestion** to generate and ingest Amazon weblogs!")
            return

        metrics = engine.compute_overview_metrics(df)

        # 4 Primary High-Contrast KPI Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="metric-container" style="border-left-color: #2563EB;">
                <div class="metric-label">Total Amazon Requests</div>
                <div class="metric-value">{metrics['total_requests']:,}</div>
                <div class="metric-sub">Partition: {selected_date}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-container" style="border-left-color: #059669;">
                <div class="metric-label">Unique Shopper IPs</div>
                <div class="metric-value">{metrics['unique_ips']:,}</div>
                <div class="metric-sub">Client sessions tracked</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="metric-container" style="border-left-color: #D97706;">
                <div class="metric-label">Mean Response Time</div>
                <div class="metric-value">{metrics['avg_response_time']} <span style="font-size: 1.1rem; color: #64748B;">ms</span></div>
                <div class="metric-sub">P50 Median: {metrics['median_response_time']} ms</div>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div class="metric-container" style="border-left-color: #10B981;">
                <div class="metric-label">HTTP Success Rate</div>
                <div class="metric-value">{metrics['success_rate']}%</div>
                <div class="metric-sub">{metrics['success_count']:,} HTTP 2xx hits</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 4 Secondary Metric Cards
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.markdown(f"""
            <div class="metric-container" style="border-left-color: #EF4444;">
                <div class="metric-label">Slow Latency Requests (≥500ms)</div>
                <div class="metric-value" style="color: #DC2626;">{metrics['slow_requests_count']:,}</div>
                <div class="metric-sub">{metrics['slow_requests_pct']}% of total traffic</div>
            </div>
            """, unsafe_allow_html=True)

        with s2:
            st.markdown(f"""
            <div class="metric-container" style="border-left-color: #6366F1;">
                <div class="metric-label">P95 Tail Latency</div>
                <div class="metric-value">{metrics['p95_response_time']} <span style="font-size: 1.1rem; color: #64748B;">ms</span></div>
                <div class="metric-sub">95th percentile SLA marker</div>
            </div>
            """, unsafe_allow_html=True)

        with s3:
            st.markdown(f"""
            <div class="metric-container" style="border-left-color: #F59E0B;">
                <div class="metric-label">4xx Client Errors</div>
                <div class="metric-value">{metrics['client_errors_count']:,}</div>
                <div class="metric-sub">Bad requests / Auth redirects</div>
            </div>
            """, unsafe_allow_html=True)

        with s4:
            st.markdown(f"""
            <div class="metric-container" style="border-left-color: #991B1B;">
                <div class="metric-label">5xx Server Failures</div>
                <div class="metric-value" style="color: #991B1B;">{metrics['server_errors_count']:,}</div>
                <div class="metric-sub">Gateway & Service errors</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # High-Contrast Charts
        col_left, col_right = st.columns([1.6, 1.4])

        with col_left:
            st.markdown("<h4 style='color: #1E293B;'>📈 Hourly Request Traffic Distribution (24-Hour Scan)</h4>", unsafe_allow_html=True)
            hourly_df = engine.compute_hourly_traffic(df)
            st.line_chart(hourly_df.set_index("hour"), color="#2563EB", use_container_width=True)

        with col_right:
            st.markdown("<h4 style='color: #1E293B;'>📊 HTTP Status Code Breakdown</h4>", unsafe_allow_html=True)
            status_df = engine.compute_status_distribution(df)
            st.bar_chart(status_df.set_index("status_code")["count"], color="#059669", use_container_width=True)

    # -------------------------------------------------------------------------
    # PAGE 2: LIVE AMAZON STREAM
    # -------------------------------------------------------------------------
    elif selected_page == "2. Live Amazon Stream":
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">
                <span>⚡</span> Live Amazon Weblog Stream
            </div>
            <div class="hero-subtitle">
                Real-time server access logs retrieved directly from Cassandra table <code>logs_by_date</code>.
            </div>
            <div style="margin-top: 10px;">
                <span class="badge-live">Live Stream Feed</span>
                <span class="badge-aws">Amazon Production Path Simulation</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not conn_ok:
            st.warning("⚠️ Cassandra is offline.")
            return

        ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 2])
        with ctrl1:
            record_limit = st.selectbox("Display Limit", [25, 50, 100, 200], index=1)
        with ctrl2:
            auto_refresh = st.checkbox("Auto-Refresh Feed", value=False)
        with ctrl3:
            search_query = st.text_input("Filter by ASIN, Path or IP", placeholder="e.g. B08N5WRWNW or /cart")

        df = load_data_for_date(engine, selected_date)
        if df.empty:
            st.info("No logs present for the selected date.")
            return

        display_df = df.copy()
        if search_query:
            display_df = display_df[
                display_df["url_path"].str.contains(search_query, case=False, na=False) |
                display_df["ip_address"].str.contains(search_query, case=False, na=False)
            ]

        display_df = display_df.head(record_limit)
        format_cols = ["event_time", "http_method", "status_code", "response_time_ms", "url_path", "ip_address", "user_agent"]
        st.dataframe(
            display_df[format_cols],
            use_container_width=True,
            column_config={
                "event_time": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss"),
                "http_method": st.column_config.TextColumn("Method", width="small"),
                "status_code": st.column_config.NumberColumn("Status", format="%d"),
                "response_time_ms": st.column_config.NumberColumn("Latency", format="%.1f ms"),
                "url_path": st.column_config.TextColumn("Amazon Endpoint / ASIN", width="medium"),
                "ip_address": st.column_config.TextColumn("Shopper IP"),
            }
        )

        if auto_refresh:
            st.caption("Live feed active. Monitoring real-time requests from Cassandra.")

    # -------------------------------------------------------------------------
    # PAGE 3: TRAFFIC & WORKLOAD
    # -------------------------------------------------------------------------
    elif selected_page == "3. Traffic & Workload":
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">
                <span>🛒</span> Amazon Traffic & Workload Analytics
            </div>
            <div class="hero-subtitle">
                Product browsing volumes, search query spikes, and 1-Click checkout request breakdown.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not conn_ok:
            st.warning("⚠️ Cassandra is offline.")
            return

        df = load_data_for_date(engine, selected_date)
        if df.empty:
            st.info("No data available.")
            return

        t1, t2 = st.columns(2)
        with t1:
            st.markdown("<h4 style='color: #1E293B;'>Diurnal Hourly Traffic Trend</h4>", unsafe_allow_html=True)
            hourly = engine.compute_hourly_traffic(df)
            st.bar_chart(hourly.set_index("hour"), color="#2563EB", use_container_width=True)

        with t2:
            st.markdown("<h4 style='color: #1E293B;'>HTTP Method Breakdown</h4>", unsafe_allow_html=True)
            methods = engine.compute_method_distribution(df)
            st.bar_chart(methods.set_index("http_method")["count"], color="#8B5CF6", use_container_width=True)

        st.markdown("---")
        st.markdown("<h4 style='color: #1E293B;'>Top Amazon Product Pages & Endpoints</h4>", unsafe_allow_html=True)
        top_urls = engine.compute_top_endpoints(df, limit=12)
        st.dataframe(top_urls, use_container_width=True)

    # -------------------------------------------------------------------------
    # PAGE 4: ERROR TRIAGE & FAILURES
    # -------------------------------------------------------------------------
    elif selected_page == "4. Error Triage & Failures":
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">
                <span>⚠️</span> Error Triage & Fault Analysis
            </div>
            <div class="hero-subtitle">
                Forensic investigation of 4xx client errors (403 WAF blocks, 404s) and 5xx server exceptions.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not conn_ok:
            st.warning("⚠️ Cassandra is offline.")
            return

        df = load_data_for_date(engine, selected_date)
        if df.empty:
            st.info("No data available.")
            return

        errors_df = df[df["status_code"] >= 400]
        total_err = len(errors_df)
        client_err = len(df[(df["status_code"] >= 400) & (df["status_code"] < 500)])
        server_err = len(df[df["status_code"] >= 500])

        e1, e2, e3 = st.columns(3)
        with e1:
            st.metric("Total Failed Invocations", f"{total_err:,}")
        with e2:
            st.metric("4xx Client Errors (401/403/404)", f"{client_err:,}")
        with e3:
            st.metric("5xx Microservice Failures (500/503)", f"{server_err:,}")

        st.markdown("---")
        if total_err > 0:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<h4 style='color: #1E293B;'>Error Frequency by Status Code</h4>", unsafe_allow_html=True)
                err_counts = errors_df["status_code"].value_counts().reset_index()
                err_counts.columns = ["status_code", "count"]
                st.bar_chart(err_counts.set_index("status_code"), color="#EF4444", use_container_width=True)

            with c2:
                st.markdown("<h4 style='color: #1E293B;'>Most Impacted URL Endpoints</h4>", unsafe_allow_html=True)
                bad_endpoints = errors_df["url_path"].value_counts().head(8).reset_index()
                bad_endpoints.columns = ["url_path", "error_count"]
                st.dataframe(bad_endpoints, use_container_width=True)

            st.markdown("---")
            st.markdown("<h4 style='color: #1E293B;'>Error Log Records (Retrieved from <code>logs_by_status</code>)</h4>", unsafe_allow_html=True)
            st.dataframe(errors_df[["event_time", "status_code", "http_method", "url_path", "ip_address", "response_time_ms"]].head(25), use_container_width=True)
        else:
            st.success("🎉 Zero HTTP errors recorded for this date!")

    # -------------------------------------------------------------------------
    # PAGE 5: LATENCY & P95 PROFILING
    # -------------------------------------------------------------------------
    elif selected_page == "5. Latency & P95 Profiling":
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">
                <span>⏱️</span> Service Latency & P95 SLA Profiling
            </div>
            <div class="hero-subtitle">
                Statistical latency modeling: Mean, Median (P50), 95th Percentile (P95), and Kernel Density Estimation.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not conn_ok:
            st.warning("⚠️ Cassandra is offline.")
            return

        df = load_data_for_date(engine, selected_date)
        if df.empty:
            st.info("No data available.")
            return

        metrics = engine.compute_overview_metrics(df)

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Average Latency", f"{metrics['avg_response_time']} ms")
        p2.metric("Median P50", f"{metrics['median_response_time']} ms")
        p3.metric("95th Percentile (P95)", f"{metrics['p95_response_time']} ms")
        p4.metric("Max Recorded Latency", f"{metrics['max_response_time']} ms")

        st.markdown("---")

        c1, c2 = st.columns([1.5, 1.5])
        with c1:
            st.markdown("<h4 style='color: #1E293B;'>Response Time Histogram & KDE Curve</h4>", unsafe_allow_html=True)
            # High-Contrast Light Figure
            plt.style.use('default')
            fig, ax = plt.subplots(figsize=(6, 3.8), facecolor='#FFFFFF')
            sns.histplot(df["response_time_ms"], bins=40, kde=True, color="#2563EB", ax=ax)
            ax.axvline(500, color="#DC2626", linestyle="--", linewidth=1.5, label="Slow Threshold (500ms)")
            ax.set_facecolor('#F8FAFC')
            ax.set_xlabel("Latency (ms)", color="#1E293B", fontsize=10, fontweight='bold')
            ax.set_ylabel("Request Count", color="#1E293B", fontsize=10, fontweight='bold')
            ax.tick_params(colors="#334155")
            ax.legend(facecolor='#FFFFFF', edgecolor='#CBD5E1', labelcolor='#0F172A')
            st.pyplot(fig)

        with c2:
            st.markdown("<h4 style='color: #1E293B;'>Amazon Endpoint Latency Benchmarks</h4>", unsafe_allow_html=True)
            top_endpoints = engine.compute_top_endpoints(df, limit=8)
            st.dataframe(top_endpoints[["url_path", "avg_latency_ms", "p95_latency_ms", "requests"]], use_container_width=True)

    # -------------------------------------------------------------------------
    # PAGE 6: SLOW REQUEST INVESTIGATION
    # -------------------------------------------------------------------------
    elif selected_page == "6. Slow Request Investigation":
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">
                <span>🐢</span> Slow Request Latency Investigation (≥500ms)
            </div>
            <div class="hero-subtitle">
                Queries Cassandra table <code>slow_requests_by_date</code> clustered by <code>response_time_ms DESC</code>.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not conn_ok:
            st.warning("⚠️ Cassandra is offline.")
            return

        slow_df = engine.fetch_slow_requests(selected_date, limit=100)

        s1, s2 = st.columns(2)
        s1.metric("Total Slow Requests in Table", f"{len(slow_df):,}")
        s2.metric("SLA Threshold", "≥ 500.0 ms")

        if slow_df.empty:
            st.info("No slow requests recorded in `slow_requests_by_date` for this date.")
        else:
            st.markdown("<h4 style='color: #1E293B;'>Slowest Requests Ranked (Descending Latency)</h4>", unsafe_allow_html=True)
            st.dataframe(
                slow_df[["response_time_ms", "event_time", "http_method", "url_path", "status_code", "ip_address"]],
                use_container_width=True,
                column_config={
                    "response_time_ms": st.column_config.NumberColumn("Response Time", format="%.2f ms"),
                    "event_time": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss"),
                }
            )

    # -------------------------------------------------------------------------
    # PAGE 7: SHOPPER IP FORENSICS
    # -------------------------------------------------------------------------
    elif selected_page == "7. Shopper IP Forensics":
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">
                <span>🔍</span> Client IP Traffic & Forensic Analysis
            </div>
            <div class="hero-subtitle">
                Audits customer traffic patterns and queries <code>logs_by_ip</code> for targeted session history.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not conn_ok:
            st.warning("⚠️ Cassandra is offline.")
            return

        df = load_data_for_date(engine, selected_date)
        if df.empty:
            st.info("No data available.")
            return

        top_ips = engine.compute_top_ips(df, limit=10)
        st.markdown("<h4 style='color: #1E293B;'>Most Active Client IP Addresses</h4>", unsafe_allow_html=True)
        st.dataframe(top_ips, use_container_width=True)

        st.markdown("---")
        st.markdown("<h4 style='color: #1E293B;'>Inspect Specific IP Audit Trail</h4>", unsafe_allow_html=True)
        available_ips = list(top_ips["ip_address"]) if not top_ips.empty else []
        selected_ip = st.selectbox("Choose IP to inspect:", available_ips if available_ips else ["None"])

        if selected_ip and selected_ip != "None":
            ip_logs = engine.fetch_logs_by_ip(selected_ip, selected_date, limit=50)
            st.write(f"Logs for IP **{selected_ip}** on **{selected_date}** ({len(ip_logs)} entries):")
            st.dataframe(ip_logs[["event_time", "http_method", "url_path", "status_code", "response_time_ms", "user_agent"]], use_container_width=True)

    # -------------------------------------------------------------------------
    # PAGE 8: CASSANDRA SCHEMA & CQL
    # -------------------------------------------------------------------------
    elif selected_page == "8. Cassandra Schema & CQL":
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">
                <span>🗄️</span> Apache Cassandra Database Architecture
            </div>
            <div class="hero-subtitle">
                Cluster metadata, single-node ring configuration, keyspace topology, and live CQL sandbox.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not conn_ok:
            st.error(f"❌ Cannot connect to Cassandra: {conn_msg}")
            return

        info = mgr.get_cluster_info()

        c1, c2, c3 = st.columns(3)
        c1.metric("Cluster Name", info.get("cluster_name", "N/A"))
        c2.metric("Release Version", info.get("release_version", "N/A"))
        c3.metric("Target Keyspace", info.get("keyspace", "N/A"))

        st.markdown("---")
        st.markdown("<h4 style='color: #1E293B;'>Configured Query-Driven Tables</h4>", unsafe_allow_html=True)

        table_details = [
            ("logs_by_date", "((log_date, hour_bucket), event_time, log_id)", "event_time DESC, log_id ASC", "Primary time-series log lookups"),
            ("logs_by_ip", "((ip_address, log_date), event_time, log_id)", "event_time DESC, log_id ASC", "Client IP forensic audits"),
            ("logs_by_status", "((log_date, status_code), event_time, log_id)", "event_time DESC, log_id ASC", "Fast HTTP error triage (4xx, 5xx)"),
            ("url_daily_counts", "((log_date), url_path, status_code)", "url_path ASC, status_code ASC", "Atomic COUNTER column request aggregation"),
            ("slow_requests_by_date", "((log_date, hour_bucket), response_time_ms, event_time, log_id)", "response_time_ms DESC, event_time DESC, log_id ASC", "High-latency bottleneck triage (>= 500ms)"),
        ]
        t_df = pd.DataFrame(table_details, columns=["Table Name", "Partition Key & Clustering", "Clustering Order", "Analytical Purpose"])
        st.dataframe(t_df, use_container_width=True)

        st.markdown("---")
        st.markdown("<h4 style='color: #1E293B;'>Live CQL Query Sandbox</h4>", unsafe_allow_html=True)
        cql_sandbox = st.text_area("Enter read-only CQL Query:", value="SELECT * FROM url_daily_counts LIMIT 10")
        if st.button("Execute CQL"):
            try:
                res = mgr.execute_query(cql_sandbox)
                st.write(f"Returned {len(res)} records:")
                st.write([dict(r._asdict()) if hasattr(r, "_asdict") else r for r in res])
            except Exception as e:
                st.error(f"CQL execution error: {e}")

    # -------------------------------------------------------------------------
    # PAGE 9: DATA PIPELINE & INGESTION
    # -------------------------------------------------------------------------
    elif selected_page == "9. Data Pipeline & Ingestion":
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">
                <span>⚙️</span> Amazon Weblog ETL Ingestion Pipeline
            </div>
            <div class="hero-subtitle">
                Synthesize Amazon access logs, execute Module 2 data cleaning, and insert into Apache Cassandra.
            </div>
        </div>
        """, unsafe_allow_html=True)

        gen_col1, gen_col2 = st.columns([1, 1])
        with gen_col1:
            record_count = st.slider("Log Volume to Ingest", min_value=1000, max_value=25000, value=5000, step=1000)
        with gen_col2:
            days_span = st.slider("Historical Range (Days)", min_value=1, max_value=7, value=2)

        inject_anomalies = st.checkbox("Inject synthetic anomalies (demonstrates preprocessor filtering)", value=True)

        if st.button("🚀 Ingest Amazon Logs into Cassandra", type="primary"):
            status_box = st.status("Running Data Pipeline...", expanded=True)

            with status_box:
                st.write(f"1. Synthesizing {record_count:,} Amazon access logs...")
                raw_df = generate_logs(num_records=record_count, days_back=days_span, include_anomalies=inject_anomalies)
                st.write(f"✓ Generated {len(raw_df):,} raw logs.")

                st.write("2. Running Module 2 Preprocessor (deduplication, IPv4 checks, UUID formatting)...")
                preprocessor = LogPreprocessor()
                clean_df, summary = preprocessor.process(raw_df)
                st.write(f"✓ Cleaned: {summary['valid_records']:,} valid, {summary['duplicate_records']:,} duplicates dropped, {summary['invalid_records']:,} invalid filtered.")

                if conn_ok:
                    st.write("3. Writing across all 5 Cassandra tables using prepared statements...")
                    p_bar = st.progress(0)

                    def update_prog(curr, tot):
                        p_bar.progress(curr / tot)

                    result = mgr.insert_batch(clean_df, progress_callback=update_prog)
                    st.write(f"✓ Cassandra Insertion Complete: {result['success']:,} records written.")
                    status_box.update(label="Ingestion Complete!", state="complete")
                else:
                    st.warning("Cassandra offline - ingestion skipped.")
                    status_box.update(label="Complete with warnings", state="error")

            st.success("🎉 Data pipeline finished! Explore the analytics pages above.")

    # -------------------------------------------------------------------------
    # PAGE 10: PROJECT DEFENSE & VIVA GUIDE
    # -------------------------------------------------------------------------
    elif selected_page == "10. Project Defense & Viva Guide":
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">
                <span>🎓</span> Academic Defense & Examination Guide
            </div>
            <div class="hero-subtitle">
                Key questions, architectural justifications, and Big Data concepts for your project evaluation.
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs(["Architecture", "Why Cassandra?", "Table Modeling", "Viva Q&A"])

        with tab1:
            st.markdown("""
            ### 🏗️ Data Flow Architecture
            ```text
            Amazon Web Traffic ---> Preprocessor (Module 2) ---> Apache Cassandra (Port 9042)
                                                                       |
                                                                       v
                                        Streamlit Dashboard <--- Analytics Engine (Module 4)
            ```
            - **Ingestion**: Raw web traffic validated and enriched with date and hour bucket partition keys.
            - **Storage**: Multi-table prepared statement inserts into 5 dedicated Cassandra tables.
            - **Retrieval**: Direct partition seeks without table scans or `ALLOW FILTERING`.
            """)

        with tab2:
            st.markdown("""
            ### ❓ Why Apache Cassandra for Amazon Weblogs?
            1. **LSM-Tree Write Path**: Cassandra appends writes to sequential CommitLogs and in-memory Memtables, achieving tens of thousands of writes per second without random disk seeks.
            2. **Horizontal Scalability**: Add more nodes to the ring as Amazon sales volume spikes on Prime Day.
            3. **Zero Single Point of Failure**: Peer-to-peer ring topology with Gossip protocol synchronization.
            """)

        with tab3:
            st.markdown(r"""
            ### 📊 The 5 Cassandra Tables
            - **`logs_by_date`**: Temporal queries partitioned by `(log_date, hour_bucket)`.
            - **`logs_by_ip`**: Shopper session forensic audits by `(ip_address, log_date)`.
            - **`logs_by_status`**: Rapid error filtering by `(log_date, status_code)`.
            - **`url_daily_counts`**: Atomic increment counters avoiding race conditions.
            - **`slow_requests_by_date`**: Latency bottlenecks $\ge 500$ ms clustered descending.
            """)

        with tab4:
            st.markdown("""
            ### 🎓 Common Professor Viva Questions

            **Q: Why not use a single table with ALLOW FILTERING?**  
            > *Answer*: `ALLOW FILTERING` triggers unpredictable cluster-wide partition scans across all nodes. In Cassandra, the fundamental rule is **Query-Driven Modeling**: create a dedicated table for each query pattern.

            **Q: What is the significance of P95 latency?**  
            > *Answer*: The 95th percentile captures the worst 5% tail latencies that averages conceal, critical for e-commerce SLAs.
            """)


if __name__ == "__main__":
    main()
