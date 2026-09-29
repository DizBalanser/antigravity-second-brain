#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  Antigravity Second Brain - Automated Setup (macOS/Linux)"
echo "========================================================"

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH!"
    echo "Please install Python 3.10+ via brew or your package manager."
    exit 1
fi

echo "[*] Checking Python Virtual Environment..."
if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

echo "[*] Activating virtual environment..."
source .venv/bin/activate

echo "[*] Installing required dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r "_system/telegram-bot/requirements.txt"

if [ ! -f "_system/.env" ]; then
    echo "[*] Creating _system/.env from template..."
    cp "_system/.env.example" "_system/.env"
    echo "[!] NOTE: Please open _system/.env and enter your TELEGRAM_BOT_TOKEN and GEMINI_API_KEY!"
else
    echo "[*] Configuration file _system/.env already exists."
fi

echo "========================================================"
echo "  Setup Complete!"
echo "========================================================"
echo "1. Open and fill in _system/.env"
echo "2. Open this folder in Google Antigravity / Obsidian"
echo "3. Start your 24/7 Telegram Assistant:"
echo "     source .venv/bin/activate && python3 _system/telegram-bot/bot.py"
echo "========================================================"
