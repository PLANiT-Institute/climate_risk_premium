import { Circle, Tooltip } from "react-leaflet";
import { getRiskColor, getRiskLevel } from "@/lib/geo/hazard-colors";
import type { RiskScenario } from "@/lib/geo/types";
import { SCENARIO_RISKS } from "@/lib/geo/types";

interface HazardOverlayProps {
  scenario: RiskScenario;
  center: [number, number];
}

export default function HazardOverlay({ scenario, center }: HazardOverlayProps) {
  const risks = SCENARIO_RISKS[scenario];

  // Base radius increases with risk level (in meters)
  const baseRadius = 3000;
  const radiusMultiplier = scenario === "baseline" ? 1 : scenario === "rcp45_2050" ? 1.5 : 2.5;
  const radius = baseRadius * radiusMultiplier;

  const riskColor = getRiskColor(risks.total);
  const riskLevel = getRiskLevel(risks.total);

  return (
    <Circle
      center={center}
      radius={radius}
      pathOptions={{
        fillColor: riskColor,
        fillOpacity: 0.15,
        color: riskColor,
        weight: 2,
        dashArray: "4, 4",
      }}
    >
      <Tooltip permanent direction="center" className="!bg-transparent !border-0 !shadow-none">
        <span
          className="text-xs font-semibold px-2 py-1 rounded"
          style={{ backgroundColor: riskColor, color: "white" }}
        >
          {riskLevel} Risk Zone
        </span>
      </Tooltip>
    </Circle>
  );
}
