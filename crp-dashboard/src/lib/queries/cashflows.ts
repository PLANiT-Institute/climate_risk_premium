import { CashflowRow, RawCashflowRow, normalizeCashflowRow } from "../supabase/types";

const cashflowCache: Record<string, CashflowRow[]> = {};

async function fetchLocalCashflow(scenario: string): Promise<CashflowRow[]> {
  if (cashflowCache[scenario]) return cashflowCache[scenario];
  try {
    const { default: data } = await import(`@/data/cashflows/${scenario}.json`);
    const rows = (data as RawCashflowRow[]).map((row) =>
      normalizeCashflowRow(row, scenario)
    );
    cashflowCache[scenario] = rows;
    return rows;
  } catch {
    return [];
  }
}

export async function getCashflows(scenario: string): Promise<CashflowRow[]> {
  if (process.env.NEXT_PUBLIC_SUPABASE_URL) {
    try {
      const { createServerClient } = await import("../supabase/server");
      const supabase = createServerClient();
      const { data, error } = await supabase
        .from("cashflow_timeseries")
        .select("*")
        .eq("scenario", scenario)
        .order("year", { ascending: true });
      if (!error && data && data.length > 0) return data as CashflowRow[];
    } catch {
      // Fall through
    }
  }
  return fetchLocalCashflow(scenario);
}

export async function getAllCashflows(): Promise<Record<string, CashflowRow[]>> {
  const scenarios = [
    "no_carbon_baseline", "baseline", "moderate_transition",
    "aggressive_transition", "moderate_physical", "high_physical",
    "combined_moderate", "combined_aggressive", "low_demand", "severe_drought",
  ];
  const result: Record<string, CashflowRow[]> = {};
  await Promise.all(
    scenarios.map(async (s) => {
      result[s] = await getCashflows(s);
    })
  );
  return result;
}
