#!/usr/bin/env bash
set -euo pipefail

echo ">>> MD2ImageBot setup starting..."

# Check python
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Please install Python 3.10+ and re-run."
  exit 1
fi

# Create venv
if [ ! -d ".venv" ]; then
  echo ">>> Creating virtual environment .venv"
  python3 -m venv .venv
fi

# Activate venv
# shellcheck disable=SC1091
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
echo ">>> Installing Python dependencies"
pip install -r requirements.txt

# Install playwright browsers (chromium)
echo ">>> Installing Playwright browsers (Chromium)"
python -m playwright install --with-deps chromium

# Bootstrap .env
if [ ! -f ".env" ]; then
  echo ">>> Preparing .env"
  cp .env.example .env

  read -rp "Enter BOT_TOKEN (from BotFather): " BOT_TOKEN
  read -rp "Enter ADMIN_IDS (comma-separated Telegram user IDs): " ADMIN_IDS
  read -rp "Public usage enabled? (true/false) [true]: " PUBLIC_ENABLED
  PUBLIC_ENABLED=${PUBLIC_ENABLED:-true}
  read -rp "Enter API_TOKEN for admin endpoints [auto-generate]: " API_TOKEN
  if [ -z "$API_TOKEN" ]; then
    API_TOKEN=$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)
  fi
  read -rp "API_HOST [0.0.0.0]: " API_HOST
  API_HOST=${API_HOST:-0.0.0.0}
  read -rp "API_PORT [8000]: " API_PORT
  API_PORT=${API_PORT:-8000}
  read -rp "Default image width in pixels [1024]: " RENDER_WIDTH
  RENDER_WIDTH=${RENDER_WIDTH:-1024}

  python - <<PY
from pathlib import Path
p = Path('.env')
txt = p.read_text(encoding='utf-8')
txt = txt.replace('BOT_TOKEN=', 'BOT_TOKEN=${BOT_TOKEN}')
txt = txt.replace('ADMIN_IDS=12345678,87654321', 'ADMIN_IDS=${ADMIN_IDS}')
txt = txt.replace('PUBLIC_ENABLED=true', 'PUBLIC_ENABLED=${PUBLIC_ENABLED}')
txt = txt.replace('API_HOST=0.0.0.0', 'API_HOST=${API_HOST}')
txt = txt.replace('API_PORT=8000', 'API_PORT=${API_PORT}')
txt = txt.replace('API_TOKEN=change-me-please', 'API_TOKEN=${API_TOKEN}')
txt = txt.replace('RENDER_WIDTH=1024', 'RENDER_WIDTH=${RENDER_WIDTH}')
p.write_text(txt, encoding='utf-8')
print('>>> Wrote .env')
PY
fi

echo ">>> Setup complete."
echo "Run the bot + API server with:"
echo "  source .venv/bin/activate && python -m src.main"
