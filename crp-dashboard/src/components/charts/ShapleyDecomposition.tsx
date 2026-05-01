"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from "recharts";
import { CHART_MARGIN, COLORS } from "@/lib/constants";
import { ScenarioResult } from "@/lib/types";

interface ShapleyDecompositionProps {
  scenarios: ScenarioResult[];
}

interface ShapleyResult {
  label: string;
  transition: number;
  physical: number;
  interaction: number;
  total: number;
}

function computeShapley(
  baseline_crp: number,
  transition_only_crp: number,
  physical_only_crp: number,
  combined_crp: number
): { transition: number; physical: number; interaction: number } {
  const transition =
    0.5 *
    (combined_crp - physical_only_crp + (transition_only_crp - baseline_crp));
  const physical =
    0.5 *
    (combined_crp - transition_only_crp + (physical_only_crp - baseline_crp));
  const interaction =
    combined_crp - transition_only_crp - physical_only_crp + baseline_crp;
  return { transition, physical, interaction };
}

export default function ShapleyDecomposition({
  scenarios,
}: ShapleyDecompositionProps) {
  const find = (name: string) => scenarios.find((s) => s.scenario === name);

  const baseline = find("baseline");
  const modTrans = find("moderate_transition");
  const aggTrans = find("aggressive_transition");
  const modPhys = find("moderate_physical");
  const highPhys = find("high_physical");
  const combMod = find("combined_moderate");
  const combAgg = find("combined_aggressive");
  const enh11th = find("enhanced_11th_plan");
  const enhComb = find("enhanced_combined");

  if (!baseline) return null;

  const results: ShapleyResult[] = [];

  // Moderate combination
  if (modTrans && modPhys && combMod) {
    const s = computeShapley(
      baseline.crp_bps,
      modTrans.crp_bps,
      modPhys.crp_bps,
      combMod.crp_bps
    );
    results.push({
      label: "Moderate",
      transition: s.transition,
      physical: s.physical,
      interaction: s.interaction,
      total: combMod.crp_bps - baseline.crp_bps,
    });
  }

  // Aggressive combination
  if (aggTrans && highPhys && combAgg) {
    const s = computeShapley(
      baseline.crp_bps,
      aggTrans.crp_bps,
      highPhys.crp_bps,
      combAgg.crp_bps
    );
    results.push({
      label: "Aggressive",
      transition: s.transition,
      physical: s.physical,
      interaction: s.interaction,
      total: combAgg.crp_bps - baseline.crp_bps,
    });
  }

  // Enhanced 11th Plan combination
  if (enh11th && highPhys && enhComb) {
    const s = computeShapley(
      baseline.crp_bps,
      enh11th.crp_bps,
      highPhys.crp_bps,
      enhComb.crp_bps
    );
    results.push({
      label: "Enhanced 11th Plan",
      transition: s.transition,
      physical: s.physical,
      interaction: s.interaction,
      total: enhComb.crp_bps - baseline.crp_bps,
    });
  }

  // NPV decomposition too
  const npvResults: ShapleyResult[] = [];
  if (modTrans && modPhys && combMod) {
    const s = computeShapley(
      baseline.npv_million,
      modTrans.npv_million,
      modPhys.npv_million,
      combMod.npv_million
    );
    npvResults.push({
      label: "Moderate",
      transition: s.transition,
      physical: s.physical,
      interaction: s.interaction,
      total: combMod.npv_million - baseline.npv_million,
    });
  }
  if (aggTrans && highPhys && combAgg) {
    const s = computeShapley(
      baseline.npv_million,
      aggTrans.npv_million,
      highPhys.npv_million,
      combAgg.npv_million
    );
    npvResults.push({
      label: "Aggressive",
      transition: s.transition,
      physical: s.physical,
      interaction: s.interaction,
      total: combAgg.npv_million - baseline.npv_million,
    });
  }
  if (enh11th && highPhys && enhComb) {
    const s = computeShapley(
      baseline.npv_million,
      enh11th.npv_million,
      highPhys.npv_million,
      enhComb.npv_million
    );
    npvResults.push({
      label: "Enhanced 11th Plan",
      transition: s.transition,
      physical: s.physical,
      interaction: s.interaction,
      total: enhComb.npv_million - baseline.npv_million,
    });
  }

  return (
    <div className="space-y-8">
      {/* CRP Decomposition */}
      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-3">
          CRP Decomposition (bps)
        </h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={results} margin={CHART_MARGIN} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis
              type="category"
              dataKey="label"
              tick={{ fontSize: 12 }}
              width={80}
            />
            <Tooltip
              formatter={(value: number, name: string) => [
                `${value.toFixed(1)} bps`,
                name === "transition"
                  ? "Transition Risk"
                  : name === "physical"
                  ? "Physical Risk"
                  : "Interaction",
              ]}
              contentStyle={{ fontSize: 12 }}
            />
            <Legend
              formatter={(value) =>
                value === "transition"
                  ? "Transition Risk"
                  : value === "physical"
                  ? "Physical Risk"
                  : "Interaction"
              }
              wrapperStyle={{ fontSize: 11 }}
            />
            <Bar dataKey="transition" stackId="a" fill={COLORS.transition} />
            <Bar dataKey="physical" stackId="a" fill={COLORS.physical} />
            <Bar
              dataKey="interaction"
              stackId="a"
              fill={COLORS.credit}
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* NPV Decomposition */}
      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-3">
          NPV Impact Decomposition ($M)
        </h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={npvResults} margin={CHART_MARGIN} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              type="number"
              tick={{ fontSize: 12 }}
              tickFormatter={(v) => `$${v.toFixed(0)}M`}
            />
            <YAxis
              type="category"
              dataKey="label"
              tick={{ fontSize: 12 }}
              width={80}
            />
            <Tooltip
              formatter={(value: number, name: string) => [
                `$${value.toFixed(0)}M`,
                name === "transition"
                  ? "Transition Risk"
                  : name === "physical"
                  ? "Physical Risk"
                  : "Interaction",
              ]}
              contentStyle={{ fontSize: 12 }}
            />
            <Legend
              formatter={(value) =>
                value === "transition"
                  ? "Transition Risk"
                  : value === "physical"
                  ? "Physical Risk"
                  : "Interaction"
              }
              wrapperStyle={{ fontSize: 11 }}
            />
            <Bar dataKey="transition" stackId="a" fill={COLORS.transition} />
            <Bar dataKey="physical" stackId="a" fill={COLORS.physical} />
            <Bar
              dataKey="interaction"
              stackId="a"
              fill={COLORS.credit}
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b-2 border-slate-200">
              <th className="p-3 text-left">Scenario</th>
              <th className="p-3 text-right">Transition (bps)</th>
              <th className="p-3 text-right">Physical (bps)</th>
              <th className="p-3 text-right">Interaction (bps)</th>
              <th className="p-3 text-right font-semibold">Total CRP (bps)</th>
              <th className="p-3 text-right">Transition %</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => {
              const total = Math.abs(r.transition) + Math.abs(r.physical) + Math.abs(r.interaction);
              const transPct = total > 0 ? (Math.abs(r.transition) / total) * 100 : 0;
              return (
                <tr key={r.label} className="border-b border-slate-100">
                  <td className="p-3 font-medium">{r.label}</td>
                  <td className="p-3 text-right font-mono text-blue-600">
                    {r.transition.toFixed(1)}
                  </td>
                  <td className="p-3 text-right font-mono text-red-600">
                    {r.physical.toFixed(1)}
                  </td>
                  <td className="p-3 text-right font-mono text-purple-600">
                    {r.interaction.toFixed(1)}
                  </td>
                  <td className="p-3 text-right font-mono font-semibold">
                    {r.total.toFixed(1)}
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${transPct}%` }}
                        />
                      </div>
                      <span className="text-xs font-mono">
                        {transPct.toFixed(0)}%
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
