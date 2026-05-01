import { CASHFLOWS } from "@/lib/generated/data";
import type { CashflowRow } from "@/lib/types";

export function getCashflows(scenario: string): CashflowRow[] {
  return (CASHFLOWS[scenario] ?? []) as unknown as CashflowRow[];
}

export function getAllCashflows(): Record<string, CashflowRow[]> {
  return CASHFLOWS as unknown as Record<string, CashflowRow[]>;
}
