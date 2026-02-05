import type { RiskScenario } from "./types";

// Risk level color scale (green -> yellow -> orange -> red)
export const RISK_COLORS = {
  veryLow: "#27ae60",   // < 0.05%
  low: "#f1c40f",       // 0.05% - 0.15%
  moderate: "#e67e22",  // 0.15% - 0.30%
  high: "#e74c3c",      // > 0.30%
} as const;

export function getRiskColor(riskPercentage: number): string {
  if (riskPercentage < 0.0005) return RISK_COLORS.veryLow;
  if (riskPercentage < 0.0015) return RISK_COLORS.low;
  if (riskPercentage < 0.003) return RISK_COLORS.moderate;
  return RISK_COLORS.high;
}

export function getRiskLevel(riskPercentage: number): string {
  if (riskPercentage < 0.0005) return "Very Low";
  if (riskPercentage < 0.0015) return "Low";
  if (riskPercentage < 0.003) return "Moderate";
  return "High";
}

// Asset type colors
export const ASSET_COLORS = {
  powerPlant: "#e74c3c",
  transmission765kV: "#3498db",
  transmissionRoute: "#9b59b6",
  substation: "#f1c40f",
} as const;

// Scenario display labels
export const SCENARIO_LABELS: Record<RiskScenario, string> = {
  baseline: "Baseline (2024)",
  rcp45_2050: "RCP4.5 (2050)",
  rcp85_2060: "RCP8.5 (2060)",
};
