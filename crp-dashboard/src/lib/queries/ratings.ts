import { CreditRatingRow } from "../supabase/types";

let cachedData: CreditRatingRow[] | null = null;

async function fetchLocalData(): Promise<CreditRatingRow[]> {
  if (cachedData) return cachedData;
  const { default: data } = await import("@/data/yearly_ratings.json");
  cachedData = data as CreditRatingRow[];
  return cachedData;
}

export async function getRatingTrajectories(): Promise<CreditRatingRow[]> {
  if (process.env.NEXT_PUBLIC_SUPABASE_URL) {
    try {
      const { createServerClient } = await import("../supabase/server");
      const supabase = createServerClient();
      const { data, error } = await supabase
        .from("credit_rating_trajectories")
        .select("*")
        .order("year", { ascending: true });
      if (!error && data && data.length > 0) return data as CreditRatingRow[];
    } catch {
      // Fall through
    }
  }
  return fetchLocalData();
}

export async function getRatingsByScenario(
  scenario: string
): Promise<CreditRatingRow[]> {
  const all = await getRatingTrajectories();
  return all.filter((r) => r.scenario === scenario);
}
