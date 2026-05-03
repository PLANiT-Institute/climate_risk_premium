#!/bin/bash
# Double-click in Finder (or run in Terminal) to launch CarbonLens.

cd "$(dirname "$0")/dashboard/carbonlens"

echo "======================================"
echo "  CarbonLens — Climate × Credit"
echo "======================================"

PORT=8888

# Kill any stale instance on the same port
lsof -ti tcp:$PORT | xargs kill -9 2>/dev/null
sleep 0.3

# Start a local HTTP server (required for loading JSX modules)
python3 -m http.server $PORT --bind 127.0.0.1 &
SERVER_PID=$!
sleep 0.4

echo "Opening http://localhost:$PORT/CarbonLens.html ..."
open "http://localhost:$PORT/CarbonLens.html"

echo ""
echo "Server running on port $PORT (PID $SERVER_PID)."
echo "Close this window to stop."
echo ""

# Keep terminal open — closing window kills the server
wait $SERVER_PID
