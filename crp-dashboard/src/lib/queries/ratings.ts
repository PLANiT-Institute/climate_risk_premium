import { YEARLY_RATINGS } from "@/lib/generated/data";
import type { CreditRatingRow } from "@/lib/types";

export function getRatingTrajectories(): CreditRatingRow[] {
  return YEARLY_RATINGS as unknown as CreditRatingRow[];
}

export function getRatingsByScenario(scenario: string): CreditRatingRow[] {
  return getRatingTrajectories().filter((r) => r.scenario === scenario);
}
