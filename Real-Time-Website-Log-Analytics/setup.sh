#!/usr/bin/env bash
# ==============================================================================
# Setup script for Ubuntu 24.04 LTS (WSL2 or Native Linux)
# Execute inside your Ubuntu terminal:
#   bash setup.sh
# ==============================================================================

set -e

echo "============================================================"
echo "  Real-Time Website Log Analytics - Ubuntu / WSL2 Setup"
echo "============================================================"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed. Please run: sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv"
    exit 1
fi
echo "[OK] Python detected: $(python3 --version)"

# Check Java
if command -v java &> /dev/null; then
    echo "[OK] Java detected: $(java -version 2>&1 | head -n 1)"
else
    echo "[WARNING] java command not directly in PATH. Cassandra relies on OpenJDK 11."
    if [ -d "/usr/lib/jvm/java-11-openjdk-amd64" ]; then
        echo "[OK] Found OpenJDK 11 at /usr/lib/jvm/java-11-openjdk-amd64"
    fi
fi

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "[INFO] Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

echo "[INFO] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env from template if missing
if [ ! -f ".env" ]; then
    echo "[INFO] Copying .env.example to .env..."
    cp .env.example .env
fi

# Check Cassandra connectivity
echo ""
echo "============================================================"
echo "  Checking Cassandra Status on 127.0.0.1:9042"
echo "============================================================"
if nc -z 127.0.0.1 9042 2>/dev/null || (exec 3<>/dev/tcp/127.0.0.1/9042) 2>/dev/null; then
    echo "[OK] Apache Cassandra is running and listening on port 9042!"
else
    echo "[WARNING] Apache Cassandra is not currently listening on port 9042."
    echo "To launch Cassandra, run:"
    echo "  export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64"
    echo "  /home/shiva/apache-cassandra-4.1.12/bin/cassandra"
fi

echo ""
echo "============================================================"
echo "  Setup Complete!"
echo "  To run the dashboard: bash run.sh"
echo "  To run unit tests:   pytest -v"
echo "============================================================"

