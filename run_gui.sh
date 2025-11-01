#!/bin/bash
# Quick launcher for eBay Card Scraper GUI

cd "$(dirname "$0")"

echo "🎴 eBay Card Scraper GUI"
echo "========================"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Launch the GUI
echo "🚀 Launching GUI..."
python3 launch_gui.py

# Deactivate venv if it was activated
if [ -d "venv" ]; then
    deactivate
fi
