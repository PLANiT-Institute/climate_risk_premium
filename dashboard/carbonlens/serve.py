#!/usr/bin/env python3
"""Minimal HTTP server with no-cache headers for local CarbonLens development.

Usage:
    python3 serve.py [port]   (default: 8888)

Adds Cache-Control: no-store so the browser always fetches fresh JS/JSX files.
"""
import os, sys
from http.server import SimpleHTTPRequestHandler, HTTPServer


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt, *args):
        # Suppress 304 noise; keep 200/404 visible
        code = args[1] if len(args) > 1 else ""
        if code not in ("304",):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    # Serve from the directory this script lives in
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with HTTPServer(("127.0.0.1", port), NoCacheHandler) as httpd:
        print(f"Serving CarbonLens on http://127.0.0.1:{port}/CarbonLens.html", flush=True)
        httpd.serve_forever()
