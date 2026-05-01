#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"

# Finder-launched .command shells start with a minimal PATH; add common Homebrew/Node locations.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Locate npm explicitly so we don't depend on PATH alone
NPM_BIN="$(command -v npm)"
if [ -z "$NPM_BIN" ]; then
    if [ -x "/opt/homebrew/bin/npm" ]; then NPM_BIN="/opt/homebrew/bin/npm"
    elif [ -x "/usr/local/bin/npm" ]; then NPM_BIN="/usr/local/bin/npm"
    else
        echo "ERROR: npm not found. Install Node.js from https://nodejs.org/"
        read -p "Press Enter to close..."
        exit 1
    fi
fi

# Verify Python venv
PY_BIN="$DIR/.venv_SH/bin/python3"
if [ ! -x "$PY_BIN" ]; then
    echo "ERROR: Python venv not found at $PY_BIN"
    echo "Run: python3 -m venv .venv_SH && .venv_SH/bin/pip install -r requirements.txt"
    read -p "Press Enter to close..."
    exit 1
fi

# Regenerate dashboard data from model
echo "Running model..."
"$PY_BIN" "$DIR/scripts/regenerate_dashboard_data.py"
if [ $? -ne 0 ]; then
    echo ""
    echo "Model failed. Fix errors above, then re-run."
    read -p "Press Enter to close..."
    exit 1
fi

# Start Next.js dev server (clear stale Turbopack cache first)
echo ""
echo "Starting dashboard..."
cd "$DIR/crp-dashboard" || exit 1
rm -rf .next
"$NPM_BIN" run dev &
NPM_PID=$!

# Open browser once server is ready
sleep 4
open http://localhost:3000

# Keep terminal open; Ctrl+C kills the dev server
wait $NPM_PID
