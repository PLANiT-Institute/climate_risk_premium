
from pathlib import Path
import pandas as pd
from src.pipeline.runner import CRPModelRunner

def main():
    base_dir = Path(".")
    runner = CRPModelRunner(base_dir)
    
    scenarios = [
        {"name": "Baseline (10th Plan)", "transition": "baseline", "physical": "baseline", "power_plan": "official_10th_plan"},
        {"name": "11th Plan Only", "transition": "baseline", "physical": "baseline", "power_plan": "official_11th_plan"},
        {"name": "11th Plan + High Physical", "transition": "baseline", "physical": "high_physical", "power_plan": "official_11th_plan"},
        {"name": "11th Plan + Extreme Physical", "transition": "baseline", "physical": "extreme_physical", "power_plan": "official_11th_plan"},
    ]
    
    results = runner.run_multi_scenario(scenarios)
    
    print("\n=== Financial Analysis Results ===")
    print(f"{'Scenario':<35} | {'NPV ($M)':<10} | {'IRR (%)':<8} | {'Min DSCR':<8} | {'CRP (bps)':<8}")
    print("-" * 85)
    
    baseline_npv = results["Baseline (10th Plan)"].metrics.npv
    
    for name, res in results.items():
        npv = res.metrics.npv / 1e6
        irr = res.metrics.irr * 100
        min_dscr = res.metrics.min_dscr
        
        # Calculate CRP (Spread increase vs Baseline)
        # Baseline spread is assumed 150 bps (A rating)
        current_spread = 150
        if res.credit_rating:
            current_spread = res.credit_rating.overall_rating.to_spread_bps()
            
        crp = current_spread - 150
        
        print(f"{name:<35} | {npv:>10.1f} | {irr:>8.1f} | {min_dscr:>8.2f} | {crp:>8.0f}")

if __name__ == "__main__":
    main()
