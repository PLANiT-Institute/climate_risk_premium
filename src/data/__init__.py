"""Data access layer."""

from src.data.data_loader import DataLoader, PlantParameters, TransitionScenario, PhysicalScenario, MarketScenario, CreditRatingGrid, load_data


def load_inputs(base_dir):
    """Legacy wrapper for DataLoader.load_all()"""
    loader = DataLoader(base_dir)
    return loader.load_all()


def get_param_value(params_dict, key, default=None):
    """Legacy helper to get parameter value from loaded data."""
    if hasattr(params_dict, 'to_dict'):
        params_dict = params_dict.to_dict()
    return params_dict.get(key, default)


__all__ = [
    "DataLoader",
    "PlantParameters",
    "TransitionScenario",
    "PhysicalScenario",
    "MarketScenario",
    "CreditRatingGrid",
    "load_data",
    "load_inputs",
    "get_param_value",
]
