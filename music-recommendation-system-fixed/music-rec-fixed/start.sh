#!/bin/bash
set -e

echo "========================================"
echo "  Music Recommendation System"
echo "========================================"

# Navigate to backend
cd "$(dirname "$0")/backend"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --break-system-packages -q 2>/dev/null || pip install -r requirements.txt -q

echo ""
echo "Starting server..."
echo "  API:      http://localhost:8000"
echo "  Frontend: http://localhost:8000/app"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Database will be auto-seeded on first run."
echo "Press Ctrl+C to stop."
echo "========================================"

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
