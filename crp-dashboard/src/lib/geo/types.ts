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
  wildfire: number;     // Plant outage from direct fire damage
  drought: number;      // Capacity derate from cooling water shortage
  heat: number;         // Efficiency loss from heat stress
  transmission: number; // Grid outage (line + substation): wildfire/typhoon/heat/flood
  capexLoss: number;    // Annual fraction of plant + line replacement value destroyed
  waterRisk: number;    // (legacy) extreme water unavailability cap
  total: number;        // Sum of channels (rough magnitude indicator)
}

export { SCENARIO_RISKS } from "@/lib/generated/data";
