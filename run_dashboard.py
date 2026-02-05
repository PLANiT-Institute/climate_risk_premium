#!/usr/bin/env python
"""
Simple script to run the Climate Risk Premium Streamlit dashboard.
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Run the Streamlit app."""
    # Use the main app location
    app_path = Path(__file__).parent / "src" / "app" / "streamlit_app.py"
    
    if not app_path.exists():
        print(f"Error: App not found at {app_path}")
        sys.exit(1)
    
    print("🔥 Starting Climate Risk Premium Dashboard...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.headless", "true"
    ])


if __name__ == "__main__":
    main()
