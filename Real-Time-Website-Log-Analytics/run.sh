#!/usr/bin/env bash
# ==============================================================================
# Run script for Ubuntu 24.04 LTS (WSL2 or Native Linux)
# Execute inside your Ubuntu terminal:
#   bash run.sh
# ==============================================================================

set -e

echo "============================================================"
echo "  Starting Real-Time Website Log Analytics Dashboard"
echo "============================================================"

# Activate virtual environment if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Check Cassandra
if nc -z 127.0.0.1 9042 2>/dev/null || (exec 3<>/dev/tcp/127.0.0.1/9042) 2>/dev/null; then
    echo "[OK] Apache Cassandra is active on 127.0.0.1:9042."
else
    echo "[WARNING] Apache Cassandra is not detected on 127.0.0.1:9042."
    echo "To start Cassandra:"
    echo "  export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64"
    echo "  /home/shiva/apache-cassandra-4.1.12/bin/cassandra"
    echo ""
    echo "Launching dashboard in offline mode..."
fi

echo ""
echo "[INFO] Starting Streamlit server on http://localhost:8501 ..."
streamlit run src/dashboard.py

