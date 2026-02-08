# Project structure and workflow

## Data flow
1. **Inputs (`data/raw/`, `data/external/`)**
   - CSV tables: plant parameters (capacity, heat rate, capex/opex, fuel prices), policy scenarios (dispatch priority, retirement schedules, carbon price paths), physical risk data (wildfire probabilities, drought/water stress indices, temperature trajectories).
2. **Processing (`src/data/`)**
   - Load and validate CSV inputs.
   - Scenario-specific parameterization (baseline vs transition vs physical).
3. **Modeling (`src/financials/`, `src/risk/`, `src/scenarios/`, `src/pipeline/`)**
   - Cash-flow engine with capacity factor, revenue, fuel, opex, capex, and retirement logic.
   - Transition + physical risk modules producing adjustments to utilization, costs, and outages.
   - Financing layer mapping expected loss to spreads/yields/required equity returns (CRP).
   - Pipeline classes orchestrating runs and exporting CSV outputs.
4. **Outputs (`data/processed/`, `src/reporting/`)**
   - CSV tables for spreads, DSCR/LLCR, NPV/IRR, and payback under baseline vs risk-adjusted cases.
   - Plots and report-ready figures used by Streamlit.

## Module sketch
- `src/data/loader.py`: load and validate CSV input tables.
- `src/scenarios/base.py`: scenario dataclasses (baseline, policy, physical risk stress).
- `src/risk/transition.py`: policy + grid constraints → capacity factor and lifetime adjustments.
- `src/risk/physical.py`: wildfire/water risk → outage rates, cost shocks; supports Monte Carlo hooks.
- `src/risk/financing.py`: expected loss to credit/equity spread mapping; CRP calculator.
- `src/financials/cashflow.py`: project cash flows, DSCR/LLCR, NPV/IRR with adjustments.
- `src/pipeline/runner.py`: class-based orchestration of model runs and CSV export.
- `src/reporting/plots.py`: visualization helpers for spreads, dispatch, and sensitivity charts.
- `src/app/streamlit_app.py`: Streamlit entry point to display tables and graphs from outputs.

## Testing approach
- Unit tests per module in `tests/` with small fixtures.
- Scenario regression tests to ensure CRP outputs remain consistent when inputs change.
- Notebook comparisons for exploratory validations before promoting logic into `src/`.
