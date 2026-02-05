"""
Data Loading Utilities.
"""
import pandas as pd
from typing import Dict, Any

def load_defaults(path: str = "data/raw/defaults.csv") -> Dict[str, Any]:
    """Load default parameters from CSV."""
    df = pd.read_csv(path)
    defaults = {}
    for _, row in df.iterrows():
        # Try to convert to float/int if possible
        val = row['value']
        try:
            if float(val).is_integer():
                val = int(val)
            else:
                val = float(val)
        except ValueError:
            pass # Keep as string
        defaults[row['parameter']] = val
    return defaults

def merge_with_defaults(user_params: Dict[str, Any]) -> Dict[str, Any]:
    """Merge user parameters with system defaults."""
    defaults = load_defaults()
    # Defaults first, then override with user params
    merged = defaults.copy()
    merged.update(user_params)
    return merged
