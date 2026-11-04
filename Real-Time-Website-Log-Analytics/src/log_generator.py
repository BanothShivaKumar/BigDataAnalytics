"""
Module 1: Real-World Amazon E-Commerce Weblog Generator
Generates high-fidelity real-world Amazon web access logs mirroring production
traffic patterns: product ASIN lookups, search queries, cart & 1-click checkout,
recommendation microservices, and Amazon mobile app / browser traffic.
"""

import os
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd


# Real-World Amazon ASIN Identifiers (Top Electronics, Books & Essentials)
AMAZON_ASINS = [
    "B08N5WRWNW",  # Apple MacBook Pro M1/M2
    "B09V3HN1KC",  # Apple iPad Air 5th Gen
    "B07XJ8C8F5",  # Sony WH-1000XM4 Wireless Headphones
    "B08L5WHFT9",  # Kindle Paperwhite (16 GB)
    "B0B9C2P675",  # Echo Dot 5th Gen Smart Speaker
    "B0C7B8S9N2",  # Fire TV Stick 4K Max
    "B09G9FPHY6",  # Apple Watch Series 9
    "B08J5F3G18",  # Logitech MX Master 3S Mouse
    "B09B8W5FW7",  # Samsung 980 PRO 2TB NVMe SSD
    "B08FC5L3RG",  # PlayStation 5 Console
]

# Real-World Amazon Search Queries
AMAZON_SEARCH_QUERIES = [
    "wireless+noise+cancelling+headphones",
    "mechanical+keyboard+rgb",
    "usb+c+docking+station+dual+monitor",
    "macbook+pro+16+inch+sleeve",
    "ergonomic+office+desk+chair",
    "4k+oled+gaming+monitor+144hz",
    "portable+power+bank+20000mah",
    "smart+home+wifi+plug",
    "kindle+paperwhite+leather+cover",
    "external+ssd+2tb+thunderbolt",
]

# Real-World Amazon Endpoints and URL Patterns
AMAZON_BASE_ENDPOINTS = [
    ("/", 0.16),                                       # Amazon Storefront / Gateway
    ("/gp/cart/view.html", 0.08),                     # Shopping Cart
    ("/gp/buy/spc/handlers/display.html", 0.07),      # 1-Click Checkout & Payment Review
    ("/ap/signin", 0.05),                             # Amazon Secure Authentication
    ("/gp/css/order-history", 0.06),                  # Order History & Tracking
    ("/api/v2/recommendations", 0.08),                # Real-time Personalized Recs Engine
    ("/api/v1/deals/lightning", 0.06),                # Lightning Deals & Flash Sales
    ("/hz/wishlist/ls", 0.03),                        # Customer Wishlist
    ("/gp/help/customer/display.html", 0.02),         # Customer Service Portal
    ("/images/I/71TPda7cwUL._AC_SL1500_.jpg", 0.04),  # CloudFront CDN Image Asset
]

# Exported URL Paths for testing & validation
URL_PATHS = [p[0] for p in AMAZON_BASE_ENDPOINTS] + [f"/gp/product/{asin}" for asin in AMAZON_ASINS]

# HTTP Methods Distribution (GET dominancy with transactional POST/PUT)
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "HEAD"]
METHOD_WEIGHTS = [0.72, 0.18, 0.05, 0.03, 0.02]

# Realistic HTTP Status Codes in E-Commerce Platforms
STATUS_CODES = [200, 201, 204, 302, 304, 400, 401, 403, 404, 500, 502, 503, 504]
STATUS_WEIGHTS = [0.68, 0.05, 0.03, 0.05, 0.04, 0.03, 0.02, 0.02, 0.04, 0.015, 0.01, 0.01, 0.005]

# Real-World User Agents (Amazon App iOS/Android, Desktop Browsers, CloudFront bot)
USER_AGENTS = [
    "Amazon.com/26.3.0.100 (iPhone; iOS 17.4; Scale/3.00; Model/iPhone15,2)",
    "Amazon/24.5.0 (Linux; U; Android 14; en_US; SM-S928B Build/UP1A.231005.007)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Amazonbot/0.1 (+https://developer.amazon.com/support/amazonbot)",
]

# Realistic Client and CloudFront Edge IP Prefixes (3 octets)
IP_PREFIXES = [
    "54.239.28.",   # AWS Amazon EC2 / CloudFront
    "205.251.192.", # Amazon Infrastructure
    "176.32.98.",   # Amazon Europe IP Range
    "72.21.215.",   # Amazon Retail Operations
    "192.168.1.",   # Local client Wi-Fi
    "10.0.4.",      # Internal VPN client
    "172.16.1.",    # Private Subnet
    "49.205.18.",   # Residential ISP (Asia-Pacific)
    "142.250.72.",  # Enterprise Gateway
    "198.51.100.",  # Public Gateway
]


def generate_random_ip() -> str:
    """Generate a realistic client IP with weighted recurring shoppers."""
    prefix = random.choice(IP_PREFIXES)
    host = random.choices(
        range(1, 255),
        weights=[12 if i in [14, 28, 45, 92, 110, 168, 204] else 1 for i in range(1, 255)]
    )[0]
    return f"{prefix}{host}"


def generate_amazon_url() -> Tuple[str, str]:
    """
    Generate authentic Amazon URL paths.
    Returns (url_path, canonical_method)
    """
    roll = random.random()
    if roll < 0.28:
        # Dynamic Product Detail Page (ASIN)
        asin = random.choice(AMAZON_ASINS)
        return f"/gp/product/{asin}", "GET"
    elif roll < 0.45:
        # Amazon Keyword Search
        query = random.choice(AMAZON_SEARCH_QUERIES)
        return f"/s?k={query}", "GET"
    elif roll < 0.55:
        # Product Reviews / Ratings
        asin = random.choice(AMAZON_ASINS)
        return f"/reviews/iframe/{asin}", "GET"
    else:
        # Standard Storefront / Cart / Checkout Endpoints
        paths, weights = zip(*AMAZON_BASE_ENDPOINTS)
        chosen_path = random.choices(paths, weights=weights)[0]
        method = "POST" if chosen_path in ["/gp/buy/spc/handlers/display.html", "/ap/signin"] and random.random() < 0.60 else "GET"
        return chosen_path, method


def generate_single_log(timestamp: datetime, force_slow: bool = False) -> Dict[str, Any]:
    """Generate a single authentic Amazon weblog record."""
    url, preferred_method = generate_amazon_url()

    if preferred_method == "POST":
        method = "POST"
    else:
        method = random.choices(HTTP_METHODS, weights=METHOD_WEIGHTS)[0]

    status = random.choices(STATUS_CODES, weights=STATUS_WEIGHTS)[0]

    # Checkout & Auth have higher security checks and occasional 401/403/503 spikes
    if "/checkout" in url or "/display.html" in url or "/signin" in url:
        if random.random() < 0.18:
            status = random.choice([400, 401, 403, 500, 503])

    # Response Time Simulation:
    # Microservices / Static CDN cache: 20ms - 180ms
    # Complex Search & Recommendations: 120ms - 420ms
    # 1-Click Checkout / Payment Gateway / Prime Day Spikes (Slow requests >= 500ms): 500ms - 3200ms
    is_slow = force_slow or (random.random() < 0.16)
    if is_slow:
        # Slow database query or payment gateway authorization
        response_time = round(random.uniform(500.0, 3150.0), 2)
    elif "/checkout" in url or "/display.html" in url:
        response_time = round(random.gauss(280.0, 60.0), 2)
        response_time = max(80.0, min(490.0, response_time))
    elif "/images/" in url or url == "/":
        response_time = round(random.gauss(65.0, 20.0), 2)
        response_time = max(15.0, min(220.0, response_time))
    else:
        response_time = round(random.gauss(155.0, 45.0), 2)
        response_time = max(25.0, min(480.0, response_time))

    # Request and Response payload sizes in bytes
    if method in ["POST", "PUT"]:
        request_size = random.randint(512, 16384)
    else:
        request_size = random.randint(128, 920)

    if status in [204, 304]:
        response_size = 0
    elif "/images/" in url:
        response_size = random.randint(24576, 262144)  # High-res product images
    else:
        response_size = random.randint(800, 75000)

    return {
        "log_id": str(uuid.uuid4()),
        "timestamp": timestamp.isoformat(),
        "ip_address": generate_random_ip(),
        "http_method": method,
        "url_path": url,
        "status_code": status,
        "response_time_ms": response_time,
        "user_agent": random.choice(USER_AGENTS),
        "request_size": request_size,
        "response_size": response_size,
    }


def generate_logs(
    num_records: int = 5000,
    days_back: int = 2,
    include_anomalies: bool = True,
    seed: Optional[int] = 42
) -> pd.DataFrame:
    """
    Generate synthetic Amazon access logs with diurnal traffic distribution.
    """
    if seed is not None:
        random.seed(seed)

    now = datetime.now()
    start_time = now - timedelta(days=days_back)
    total_seconds = int((now - start_time).total_seconds())

    records: List[Dict[str, Any]] = []

    for _ in range(num_records):
        offset_seconds = random.randint(0, max(1, total_seconds))
        record_time = start_time + timedelta(seconds=offset_seconds)
        record = generate_single_log(record_time)
        records.append(record)

    df = pd.DataFrame(records)

    # Sort chronologically
    df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp_dt").drop(columns=["timestamp_dt"]).reset_index(drop=True)

    if include_anomalies and len(df) > 50:
        # Inject controlled anomalies (duplicates, missing fields, invalid ranges) for Module 2 demo
        dup_count = max(3, int(num_records * 0.01))
        dups = df.sample(dup_count).copy()
        df = pd.concat([df, dups], ignore_index=True)

        missing_indices = random.sample(range(len(df)), max(2, int(num_records * 0.005)))
        for idx in missing_indices:
            col_to_blank = random.choice(["ip_address", "url_path", "user_agent"])
            df.loc[idx, col_to_blank] = None

        bad_status_idx = random.sample(range(len(df)), max(2, int(num_records * 0.004)))
        for idx in bad_status_idx:
            df.loc[idx, "status_code"] = random.choice([999, -1, 0])

        bad_latency_idx = random.sample(range(len(df)), max(2, int(num_records * 0.004)))
        for idx in bad_latency_idx:
            df.loc[idx, "response_time_ms"] = -80.0

    return df


def save_logs_to_csv(df: pd.DataFrame, file_path: str) -> str:
    """Save generated logs DataFrame to a CSV file."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    df.to_csv(file_path, index=False)
    return file_path


if __name__ == "__main__":
    print(f"Generating 5,000 real-world Amazon e-commerce access logs...")
    sample_df = generate_logs(num_records=5000, days_back=2)
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "website_logs.csv")
    saved_path = save_logs_to_csv(sample_df, output_path)
    print(f"Successfully generated {len(sample_df)} Amazon logs and saved to {saved_path}")
