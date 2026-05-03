#!/bin/bash
# Double-click in Finder (or run in Terminal) to launch CarbonLens.

cd "$(dirname "$0")"

echo "======================================"
echo "  CarbonLens — Climate × Credit"
echo "======================================"

# Open CarbonLens directly in the default browser
open "dashboard/carbonlens/CarbonLens.html"

echo "CarbonLens opened in your browser."
echo "(No server required — runs entirely in-browser.)"
