"use client";

import { MapContainer, TileLayer, LayersControl } from "react-leaflet";
import { useEffect, useState } from "react";
import type { FeatureCollection, Feature, Polygon, LineString, Point } from "geojson";
import "leaflet/dist/leaflet.css";

import PowerPlantLayer from "./layers/PowerPlantLayer";
import TransmissionLayer from "./layers/TransmissionLayer";
import SubstationLayer from "./layers/SubstationLayer";
import HazardOverlay from "./layers/HazardOverlay";
import Legend from "./controls/Legend";
import type {
  RiskScenario,
  PowerPlantProperties,
  TransmissionLineProperties,
  SubstationProperties,
} from "@/lib/geo/types";
import { SCENARIO_LABELS } from "@/lib/geo/hazard-colors";

interface Props {
  scenario: RiskScenario;
  onScenarioChange?: (scenario: RiskScenario) => void;
  showControls?: boolean;
}

export default function PhysicalRiskMap({
  scenario,
  onScenarioChange,
  showControls = true,
}: Props) {
  const [geoData, setGeoData] = useState<FeatureCollection | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/geo/samcheok_power_grid.geojson")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load GeoJSON");
        return res.json();
      })
      .then(setGeoData)
      .catch((err) => setError(err.message));
  }, []);

  // Samcheok plant center coordinates
  const center: [number, number] = [37.408, 129.174];

  // Parse features by type
  const powerPlant = geoData?.features.find(
    (f) => f.geometry.type === "Polygon" && f.properties?.capacity_mw
  ) as Feature<Polygon, PowerPlantProperties> | undefined;

  const substation = geoData?.features.find(
    (f) => f.geometry.type === "Point" && f.properties?.type === "substation"
  ) as Feature<Point, SubstationProperties> | undefined;

  const transmission765kV = geoData?.features.find(
    (f) => f.geometry.type === "LineString" && f.properties?.voltage_kv === 765
  ) as Feature<LineString, TransmissionLineProperties> | undefined;

  const transmissionRoute = geoData?.features.find(
    (f) => f.geometry.type === "LineString" && f.properties?.from && f.properties?.to
  ) as Feature<LineString, TransmissionLineProperties> | undefined;

  if (error) {
    return (
      <div className="h-[500px] w-full rounded-lg bg-red-50 flex items-center justify-center">
        <p className="text-red-600">Error loading map: {error}</p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Scenario Toggle */}
      {showControls && onScenarioChange && (
        <div className="absolute top-4 right-4 z-[1000] bg-white rounded-lg shadow-lg p-2">
          <div className="flex gap-1">
            {(["baseline", "rcp45_2050", "rcp85_2060"] as RiskScenario[]).map((s) => (
              <button
                key={s}
                onClick={() => onScenarioChange(s)}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                  scenario === s
                    ? "bg-teal-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {SCENARIO_LABELS[s]}
              </button>
            ))}
          </div>
        </div>
      )}

      <MapContainer
        center={center}
        zoom={10}
        className="h-[500px] w-full rounded-lg"
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <LayersControl position="topright">
          {/* Hazard Zone Overlay */}
          <LayersControl.Overlay checked name="Risk Zone">
            <HazardOverlay scenario={scenario} center={center} />
          </LayersControl.Overlay>

          {/* Power Plant */}
          {powerPlant && (
            <LayersControl.Overlay checked name="Samcheok Plant">
              <PowerPlantLayer feature={powerPlant} />
            </LayersControl.Overlay>
          )}

          {/* 765kV Transmission Line */}
          {transmission765kV && (
            <LayersControl.Overlay checked name="765kV Line">
              <TransmissionLayer feature={transmission765kV} lineType="765kV" />
            </LayersControl.Overlay>
          )}

          {/* Plant to Substation Route */}
          {transmissionRoute && (
            <LayersControl.Overlay checked name="Plant-Substation Route">
              <TransmissionLayer feature={transmissionRoute} lineType="route" />
            </LayersControl.Overlay>
          )}

          {/* Substation */}
          {substation && (
            <LayersControl.Overlay checked name="Sintaebaek Substation">
              <SubstationLayer feature={substation} />
            </LayersControl.Overlay>
          )}
        </LayersControl>
      </MapContainer>

      {/* Legend */}
      <Legend scenario={scenario} />
    </div>
  );
}
