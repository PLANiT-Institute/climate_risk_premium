import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print(f"Python path: {sys.path}")

try:
    print("Attempting to import src.climada.hazards...")
    import src.climada.hazards
    print("Successfully imported src.climada.hazards")
    print(f"src.climada.hazards file: {src.climada.hazards.__file__}")
except ImportError as e:
    print(f"Failed to import src.climada.hazards: {e}")

try:
    print("Attempting to import load_climada_hazards from src.climada.hazards...")
    from src.climada.hazards import load_climada_hazards
    print("Successfully imported load_climada_hazards")
except ImportError as e:
    print(f"Failed to import load_climada_hazards: {e}")

try:
    print("Attempting to import get_hazard_description from src.climada.hazards...")
    from src.climada.hazards import get_hazard_description
    print("Successfully imported get_hazard_description")
except ImportError as e:
    print(f"Failed to import get_hazard_description: {e}")
