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
  wildfire: number;   // CLIMADA AAI → outage_rate
  drought: number;    // PhysRisk impact_mean
  waterRisk: number;  // PhysRisk impact_mean
  total: number;      // Combined CF impact
}

export const SCENARIO_RISKS: Record<RiskScenario, HazardRisk> = {
  baseline: { wildfire: 0.0000139, drought: 0.000938, waterRisk: 0.0, total: 0.00095 },
  ssp126_2040: { wildfire: 0.0000469, drought: 0.002569, waterRisk: 0.005592, total: 0.0082 },
  ssp585_2050: { wildfire: 0.0000139, drought: 0.001007, waterRisk: 0.005457, total: 0.0065 },
};
