import { ScenarioResult } from "../supabase/types";

let cachedData: ScenarioResult[] | null = null;

async function fetchLocalData(): Promise<ScenarioResult[]> {
  if (cachedData) return cachedData;
  const { default: data } = await import("@/data/scenario_comparison.json");
  cachedData = data as ScenarioResult[];
  return cachedData;
}

export async function getScenarioResults(): Promise<ScenarioResult[]> {
  if (process.env.NEXT_PUBLIC_SUPABASE_URL) {
    try {
      const { createServerClient } = await import("../supabase/server");
      const supabase = createServerClient();
      const { data, error } = await supabase
        .from("scenario_results")
        .select("*")
        .order("rating_numeric", { ascending: true });
      if (!error && data && data.length > 0) return data as ScenarioResult[];
    } catch {
      // Fall through to local data
    }
  }
  return fetchLocalData();
}

export async function getScenarioByName(
  scenario: string
): Promise<ScenarioResult | null> {
  const results = await getScenarioResults();
  return results.find((r) => r.scenario === scenario) ?? null;
}
