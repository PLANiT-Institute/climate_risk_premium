export const COLORS = {
  primary: "#1a5f7a",
  secondary: "#159895",
  accent: "#57c5b6",
  warning: "#f39c12",
  danger: "#e74c3c",
  success: "#27ae60",
  transition: "#3498db",
  physical: "#e74c3c",
  cashflow: "#27ae60",
  credit: "#9b59b6",
} as const;

export const RATING_COLORS: Record<string, string> = {
  AAA: "#006400",
  AA: "#228B22",
  A: "#32CD32",
  BBB: "#90EE90",
  BB: "#FFD700",
  B: "#FFA500",
  CCC: "#FF6347",
  CC: "#FF4500",
  C: "#DC143C",
  D: "#8B0000",
};

export const RATING_SPREADS: Record<string, number> = {
  AAA: 50,
  AA: 100,
  A: 150,
  BBB: 250,
  BB: 400,
  B: 600,
  CCC: 900,
  CC: 1500,
  C: 2500,
  D: 5000,
};

export const SCENARIO_LABELS: Record<string, string> = {
  no_carbon_baseline: "No-Carbon Baseline",
  baseline: "Baseline",
  moderate_transition: "Moderate Transition",
  aggressive_transition: "Aggressive Transition",
  moderate_physical: "Moderate Physical",
  high_physical: "High Physical",
  combined_moderate: "Combined Moderate",
  combined_aggressive: "Combined Aggressive",
  low_demand: "Low Demand",
  severe_drought: "Severe Drought",
  enhanced_11th_plan: "Enhanced 11th Plan",
  enhanced_combined: "Enhanced Combined",
};

export const SCENARIO_COLORS: Record<string, string> = {
  no_carbon_baseline: "#95a5a6",
  baseline: "#1a5f7a",
  moderate_transition: "#3498db",
  aggressive_transition: "#2c3e50",
  moderate_physical: "#e67e22",
  high_physical: "#e74c3c",
  combined_moderate: "#9b59b6",
  combined_aggressive: "#8e44ad",
  low_demand: "#f39c12",
  severe_drought: "#c0392b",
  enhanced_11th_plan: "#d63031",
  enhanced_combined: "#6c5ce7",
};

export const INVESTMENT_GRADE_RATINGS = ["AAA", "AA", "A", "BBB"];

export const CHART_MARGIN = { top: 20, right: 30, left: 20, bottom: 5 };
