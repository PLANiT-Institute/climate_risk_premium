#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"

# Regenerate dashboard data from model
echo "Running model..."
"$DIR/.venv_SH/bin/python3" "$DIR/scripts/regenerate_dashboard_data.py"
if [ $? -ne 0 ]; then
    echo ""
    echo "Model failed. Fix errors above, then re-run."
    read -p "Press Enter to close..."
    exit 1
fi

# Start Next.js dev server (clear stale Turbopack cache first)
echo ""
echo "Starting dashboard..."
cd "$DIR/crp-dashboard"
rm -rf .next
npm run dev &
NPM_PID=$!

# Open browser once server is ready
sleep 3
open http://localhost:3000

# Keep terminal open; Ctrl+C kills the dev server
wait $NPM_PID
