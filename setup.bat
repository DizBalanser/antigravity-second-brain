@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   Antigravity Second Brain - Automated Setup (Windows)
echo ========================================================

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

echo [*] Checking Python Virtual Environment...
if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
)

echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [*] Installing required dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r "_system\telegram-bot\requirements.txt"

if not exist "_system\.env" (
    echo [*] Creating _system\.env from template...
    copy "_system\.env.example" "_system\.env" >nul
    echo [!] NOTE: Please open _system\.env and enter your TELEGRAM_BOT_TOKEN and GEMINI_API_KEY!
) else (
    echo [*] Configuration file _system\.env already exists.
)

echo ========================================================
echo   Setup Complete!
echo ========================================================
echo 1. Open and fill in _system\.env
echo 2. Open this folder in Google Antigravity / Obsidian
echo 3. Start your 24/7 Telegram Assistant:
echo      .venv\Scripts\python _system\telegram-bot\bot.py
echo ========================================================
pause
