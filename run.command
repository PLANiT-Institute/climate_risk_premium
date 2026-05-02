#!/bin/bash
# Double-click in Finder (or run in Terminal) to launch the CRP Streamlit dashboard.

cd "$(dirname "$0")"

echo "======================================"
echo "  Climate Risk Premium — Starting"
echo "======================================"

# Kill any stale instance
pkill -f "streamlit run dashboard/app.py" 2>/dev/null
sleep 1

# Install / sync dependencies if needed
uv sync --quiet 2>/dev/null || true

# Launch Streamlit
echo "Opening http://localhost:8501 ..."
uv run streamlit run dashboard/app.py \
  --server.headless false \
  --browser.gatherUsageStats false
