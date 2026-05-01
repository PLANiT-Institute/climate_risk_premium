import type { Feature, FeatureCollection, Geometry, GeoJsonProperties } from "geojson";

export interface PowerPlantProperties {
  id?: string;
  name: string;
  capacity_mw?: string;
  source?: string;
  method?: string;
  center_lon?: number;
  center_lat?: number;
  source_file?: string;
}

export interface SubstationProperties {
  name: string;
  type: "substation";
  source_file?: string;
}

export interface TransmissionLineProperties {
  id?: string;
  voltage_kv?: number;
  cables?: string;
  circuits?: string;
  description?: string;
  start_lon?: number;
  start_lat?: number;
  end_lon?: number;
  end_lat?: number;
  source_file?: string;
  name?: string;
  from?: string;
  to?: string;
}

export type PowerGridFeature =
  | Feature<Geometry, PowerPlantProperties>
  | Feature<Geometry, SubstationProperties>
  | Feature<Geometry, TransmissionLineProperties>;

export type PowerGridGeoJSON = FeatureCollection<Geometry, GeoJsonProperties>;

export type RiskScenario = "baseline" | "ssp126_2040" | "ssp585_2050";

export interface HazardRisk {
  wildfire: number;   // CLIMADA event frequency -> outage_rate
  drought: number;    // PhysRisk expected impact -> derate
  waterRisk: number;  // PhysRisk expected impact -> water cap
  total: number;      // Combined CF impact
}

export const SCENARIO_RISKS: Record<RiskScenario, HazardRisk> = {
  // Updated from model output (2025 values, annualized impact on generation capacity)
  // baseline: SSP1-2.6 (2024) - Optimistic climate pathway
  baseline: { wildfire: 0.000307, drought: 0.000938, waterRisk: 0.0, total: 0.00121 },
  // ssp126_2040: SSP1-2.6 (2040) - Low emission scenario, mid-century
  // Uses RCP4.5 climate factors applied to baseline wildfire
  ssp126_2040: { wildfire: 0.000307, drought: 0.002569, waterRisk: 0.005592, total: 0.00843 },
  // ssp585_2050: SSP5-8.5 (2050) - High emission scenario, late century
  // Uses direct RCP8.5 wildfire projections (lower than baseline due to projection data)
  ssp585_2050: { wildfire: 0.000096, drought: 0.001007, waterRisk: 0.005457, total: 0.00674 },
};
