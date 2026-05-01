import { SCENARIO_COMPARISON } from "@/lib/generated/data";
import type { ScenarioResult } from "@/lib/types";

export function getScenarioResults(): ScenarioResult[] {
  return SCENARIO_COMPARISON as unknown as ScenarioResult[];
}

export function getScenarioByName(scenario: string): ScenarioResult | null {
  return getScenarioResults().find((r) => r.scenario === scenario) ?? null;
}
