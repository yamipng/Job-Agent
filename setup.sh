#!/usr/bin/env bash
# ================================================
# Job Agent — First-time setup script
# Run: bash setup.sh
# ================================================

set -e

echo ""
echo "================================================"
echo "  JOB AGENT — Setup"
echo "================================================"
echo ""

# 1. Python deps
echo "[1/4] Installing Python dependencies..."
pip install -r requirements.txt

# 2. Playwright browser
echo ""
echo "[2/4] Installing Playwright Chromium browser..."
playwright install chromium

# 3. Create required directories
echo ""
echo "[3/4] Creating data/ and sessions/ directories..."
mkdir -p data sessions data/cover_letters

# 4. Config file
echo ""
echo "[4/4] Setting up config..."
if [ ! -f config.json ]; then
    cp config.example.json config.json
    echo "  config.json created from template."
    echo "  ⚠️  Open config.json and add your ANTHROPIC_API_KEY before running the agent."
else
    echo "  config.json already exists — skipping."
fi

echo ""
echo "================================================"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit config.json — add your Anthropic API key"
echo "  2. Authenticate platforms (one-time):"
echo "     python agent/auth.py --platform linkedin"
echo "     python agent/auth.py --platform indeed"
echo "     python agent/auth.py --platform handshake"
echo "  3. Start the dashboard:"
echo "     python server.py"
echo "     Then open http://localhost:5000"
echo "================================================"
echo ""
