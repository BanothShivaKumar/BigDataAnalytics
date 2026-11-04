@echo off
REM ============================================================================
REM Windows Setup Script for Real-Time Website Log Analytics
REM Run in Windows Command Prompt (cmd) or Windows PowerShell
REM ============================================================================

echo ============================================================
echo   Real-Time Website Log Analytics - Windows Setup
echo ============================================================

REM Check Python availability
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    exit /b 1
)
echo [OK] Python detected:
python --version

REM Create virtual environment if requested, or install requirements
if not exist ".venv" (
    echo [INFO] Creating Python virtual environment in .venv...
    python -m venv .venv
)

if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo [INFO] Installing required Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Copy .env.example to .env if not exists
if not exist ".env" (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env >nul
)

echo.
echo ============================================================
echo   Checking Apache Cassandra Connectivity (127.0.0.1:9042)
echo ============================================================
python -c "import socket; s = socket.socket(); s.settimeout(2.0); res = s.connect_ex(('127.0.0.1', 9042)); s.close(); exit(res)" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Apache Cassandra is running and reachable on port 9042!
) else (
    echo [WARNING] Apache Cassandra is not currently responding on 127.0.0.1:9042.
    echo If running in WSL2 Ubuntu, start it with:
    echo   wsl -d Ubuntu bash -c "/home/shiva/apache-cassandra-4.1.12/bin/cassandra"
)

echo.
echo ============================================================
echo   Setup Complete!
echo   To launch the dashboard, run: run.bat
echo   To run automated tests, run: pytest -v
echo ============================================================

