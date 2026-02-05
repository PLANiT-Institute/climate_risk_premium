
import sys
import os
sys.path.append(os.getcwd())

from src.risk.physical import get_physical_risk_engine, PhysicalAdjustments
from src.utils.data_loader import merge_with_defaults
from src.financials.cashflow import compute_cashflows_timeseries
from src.risk.transition import TransitionAdjustments, apply_transition
from src.scenarios import TransitionScenario

def test_physical_refactor():
    print("Testing Physical Risk Engine...")
    engine = get_physical_risk_engine()
    
    # Test valid scenario
    adj = engine.calculate_adjustments({}, "High Physical Risk (Corrected)", 2030)
    print(f"High Scen 2030 Impact: Outage={adj.outage_rate:.4f}, Derate={adj.capacity_derate:.4f}")
    assert adj.outage_rate > 0.0, "Outage rate should be positive"
    
    # Test fallback
    adj_base = engine.calculate_adjustments({}, "NonExistent", 2024)
    print(f"Fallback Impact: Outage={adj_base.outage_rate:.4f}")
    assert adj_base.outage_rate == 0.0005, "Should fall back to baseline 0.05%"

def test_cashflow_refactor():
    print("\nTesting Cashflow Refactor...")
    plant_params = merge_with_defaults({"capacity_mw": 2100})
    
    trans_adj = TransitionAdjustments(capacity_factor=0.85, operating_years=30)
    phys_adj = PhysicalAdjustments(outage_rate=0.01, capacity_derate=0.0, efficiency_loss=0.0)
    trans_scen = TransitionScenario(name="Test", dispatch_priority_penalty=0.0, retirement_years=30)
    
    cf = compute_cashflows_timeseries(
        plant_params,
        trans_scen,
        trans_adj,
        phys_adj,
        start_year=2025
    )
    print(f"Total Revenue: ${cf.revenue.sum()/1e9:.2f}B")
    assert cf.revenue.sum() > 0, "Revenue should be positive"

if __name__ == "__main__":
    test_physical_refactor()
    test_cashflow_refactor()
    print("\nALL TESTS PASSED")
