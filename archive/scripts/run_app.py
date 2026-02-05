import os
import sys
from streamlit.web import cli as stcli

if __name__ == "__main__":
    # Ensure the project root is in sys.path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Set the script path to the streamlit app
    script_path = os.path.join(project_root, "src", "app", "streamlit_app.py")
    
    # Construct arguments for streamlit run
    sys.argv = ["streamlit", "run", script_path]
    
    print(f"Launching Streamlit app from: {script_path}")
    print(f"Python path: {sys.path[0]}")
    
    sys.exit(stcli.main())
