"use client";

import { MapContainer, TileLayer, LayersControl, useMap } from "react-leaflet";
import { useEffect, useMemo, useState } from "react";
import { latLngBounds } from "leaflet";
import type { FeatureCollection, Feature, Polygon, LineString, Point, Position } from "geojson";
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

const DEFAULT_CENTER: [number, number] = [37.408, 129.174];
const REGIONAL_LINE_THRESHOLD_KM = 90;
const LOCAL_765_SEGMENT_RADIUS_KM = 22;

function toLatLng(coord: Position): [number, number] {
  return [coord[1], coord[0]];
}

function haversineKm(a: Position, b: Position): number {
  const [lat1, lon1] = toLatLng(a);
  const [lat2, lon2] = toLatLng(b);
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const rLat1 = toRad(lat1);
  const rLat2 = toRad(lat2);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(rLat1) * Math.cos(rLat2) * Math.sin(dLon / 2) ** 2;

  return 6371 * (2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h)));
}

function trimRegionalLine(feature: Feature<LineString, TransmissionLineProperties>) {
  const coords = feature.geometry.coordinates;
  if (coords.length < 2) return feature;

  const start = coords[0];
  const end = coords[coords.length - 1];
  const spanKm = haversineKm(start, end);
  if (spanKm <= REGIONAL_LINE_THRESHOLD_KM) return feature;

  const localCoords: Position[] = [];
  for (const coord of coords) {
    const isLocal = haversineKm(start, coord) <= LOCAL_765_SEGMENT_RADIUS_KM;
    if (isLocal || localCoords.length < 2) {
      localCoords.push(coord);
      continue;
    }
    break;
  }

  if (localCoords.length < 2 || localCoords.length === coords.length) return feature;

  return {
    ...feature,
    properties: {
      ...feature.properties,
      name: feature.properties?.name || "765kV Regional Corridor (Local Segment)",
    },
    geometry: {
      ...feature.geometry,
      coordinates: localCoords,
    },
  };
}

interface AutoFitBoundsProps {
  powerPlant?: Feature<Polygon, PowerPlantProperties>;
  substation?: Feature<Point, SubstationProperties>;
  transmissionRoute?: Feature<LineString, TransmissionLineProperties>;
  transmission765kV?: Feature<LineString, TransmissionLineProperties>;
}

function AutoFitBounds({
  powerPlant,
  substation,
  transmissionRoute,
  transmission765kV,
}: AutoFitBoundsProps) {
  const map = useMap();

  useEffect(() => {
    const points: [number, number][] = [];

    if (powerPlant) {
      for (const ring of powerPlant.geometry.coordinates) {
        for (const coord of ring) points.push([coord[1], coord[0]]);
      }
    }

    if (substation) {
      const [lon, lat] = substation.geometry.coordinates;
      points.push([lat, lon]);
    }

    if (transmissionRoute) {
      for (const coord of transmissionRoute.geometry.coordinates) {
        points.push([coord[1], coord[0]]);
      }
    }

    if (transmission765kV) {
      for (const coord of transmission765kV.geometry.coordinates) {
        points.push([coord[1], coord[0]]);
      }
    }

    if (points.length < 2) return;

    map.fitBounds(latLngBounds(points), {
      padding: [20, 20],
      maxZoom: 11,
      animate: false,
    });
  }, [map, powerPlant, substation, transmissionRoute, transmission765kV]);

  return null;
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

  // Parse features by type
  const powerPlant = useMemo(
    () =>
      geoData?.features.find(
        (f) => f.geometry.type === "Polygon" && f.properties?.capacity_mw
      ) as Feature<Polygon, PowerPlantProperties> | undefined,
    [geoData]
  );

  const substation = useMemo(
    () =>
      geoData?.features.find(
        (f) => f.geometry.type === "Point" && f.properties?.type === "substation"
      ) as Feature<Point, SubstationProperties> | undefined,
    [geoData]
  );

  const transmissionRoute = useMemo(
    () =>
      geoData?.features.find(
        (f) => f.geometry.type === "LineString" && f.properties?.from && f.properties?.to
      ) as Feature<LineString, TransmissionLineProperties> | undefined,
    [geoData]
  );

  const transmission765kV = useMemo(() => {
    const line = geoData?.features.find(
      (f) => f.geometry.type === "LineString" && f.properties?.voltage_kv === 765
    ) as Feature<LineString, TransmissionLineProperties> | undefined;

    return line ? trimRegionalLine(line) : undefined;
  }, [geoData]);

  const center: [number, number] = powerPlant?.properties?.center_lat && powerPlant?.properties?.center_lon
    ? [powerPlant.properties.center_lat, powerPlant.properties.center_lon]
    : DEFAULT_CENTER;

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
            {(["baseline", "ssp126_2040", "ssp585_2050"] as RiskScenario[]).map((s) => (
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

        <AutoFitBounds
          powerPlant={powerPlant}
          substation={substation}
          transmissionRoute={transmissionRoute}
          transmission765kV={transmission765kV}
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
            <LayersControl.Overlay checked name="765kV Corridor (Local)">
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
