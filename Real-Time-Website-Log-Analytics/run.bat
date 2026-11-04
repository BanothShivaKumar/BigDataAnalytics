@echo off
REM ============================================================================
REM Windows Run Script for Real-Time Website Log Analytics
REM Run in Windows Command Prompt (cmd) or Windows PowerShell
REM ============================================================================

echo ============================================================
echo   Launching Real-Time Website Log Analytics Dashboard
echo ============================================================

if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment .venv...
    call .venv\Scripts\activate.bat
)

REM Check Cassandra
python -c "import socket; s = socket.socket(); s.settimeout(2.0); res = s.connect_ex(('127.0.0.1', 9042)); s.close(); exit(res)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Apache Cassandra is not detected on 127.0.0.1:9042!
    echo If running via WSL2, please launch Cassandra in your Ubuntu terminal:
    echo   wsl -d Ubuntu bash -c "/home/shiva/apache-cassandra-4.1.12/bin/cassandra"
    echo.
    echo Launching dashboard in offline mode...
) else (
    echo [OK] Cassandra is live on 127.0.0.1:9042.
)

echo.
echo [INFO] Starting Streamlit server...
echo [INFO] Local URL: http://localhost:8501
echo.
streamlit run src/dashboard.py

