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

export type RiskScenario = "baseline" | "rcp45_2050" | "rcp85_2060";

export interface HazardRisk {
  wildfire: number;
  flood: number;
  slr: number;
  total: number;
}

export const SCENARIO_RISKS: Record<RiskScenario, HazardRisk> = {
  baseline: { wildfire: 0.00055, flood: 0.00003, slr: 0.0, total: 0.00058 },
  rcp45_2050: { wildfire: 0.00082, flood: 0.00003, slr: 0.00042, total: 0.00127 },
  rcp85_2060: { wildfire: 0.0022, flood: 0.00003, slr: 0.00161, total: 0.00384 },
};
