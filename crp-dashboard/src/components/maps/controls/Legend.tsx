import { ASSET_COLORS, RISK_COLORS, SCENARIO_LABELS } from "@/lib/geo/hazard-colors";
import type { RiskScenario, HazardRisk } from "@/lib/geo/types";
import { SCENARIO_RISKS } from "@/lib/geo/types";

interface LegendProps {
  scenario: RiskScenario;
}

export default function Legend({ scenario }: LegendProps) {
  const risks = SCENARIO_RISKS[scenario];

  return (
    <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-4 z-[1000] text-sm max-w-xs">
      <h3 className="font-semibold text-slate-800 mb-3 border-b pb-2">
        {SCENARIO_LABELS[scenario]}
      </h3>

      {/* Asset Types */}
      <div className="mb-3">
        <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Assets</p>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded"
              style={{ backgroundColor: ASSET_COLORS.powerPlant, opacity: 0.6 }}
            />
            <span className="text-slate-700">Samcheok Power Plant</span>
          </div>
          <div className="flex items-center gap-2">
            <div
              className="w-4 h-1 rounded"
              style={{ backgroundColor: ASSET_COLORS.transmission765kV }}
            />
            <span className="text-slate-700">765kV Transmission</span>
          </div>
          <div className="flex items-center gap-2">
            <div
              className="w-4 h-1 rounded border-dashed border-2"
              style={{ borderColor: ASSET_COLORS.transmissionRoute }}
            />
            <span className="text-slate-700">Plant-Substation Route</span>
          </div>
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full border-2"
              style={{ backgroundColor: ASSET_COLORS.substation, borderColor: "#333" }}
            />
            <span className="text-slate-700">Sintaebaek Substation</span>
          </div>
        </div>
      </div>

      {/* Risk Levels */}
      <div className="mb-3">
        <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Risk Levels</p>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: RISK_COLORS.veryLow }} />
            <span className="text-slate-700">&lt; 0.05% (Very Low)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: RISK_COLORS.low }} />
            <span className="text-slate-700">0.05-0.15% (Low)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: RISK_COLORS.moderate }} />
            <span className="text-slate-700">0.15-0.30% (Moderate)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: RISK_COLORS.high }} />
            <span className="text-slate-700">&gt; 0.30% (High)</span>
          </div>
        </div>
      </div>

      {/* Current Scenario Risk */}
      <div className="border-t pt-2">
        <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">CF Loss</p>
        <div className="grid grid-cols-2 gap-1 text-xs">
          <span className="text-slate-600">Wildfire:</span>
          <span className="font-mono text-right">{(risks.wildfire * 100).toFixed(3)}%</span>
          <span className="text-slate-600">Drought:</span>
          <span className="font-mono text-right">{(risks.drought * 100).toFixed(3)}%</span>
          <span className="text-slate-600">Water Risk:</span>
          <span className="font-mono text-right">{(risks.waterRisk * 100).toFixed(3)}%</span>
          <span className="text-slate-600 font-semibold">Total:</span>
          <span className="font-mono text-right font-semibold">{(risks.total * 100).toFixed(3)}%</span>
        </div>
      </div>
    </div>
  );
}
