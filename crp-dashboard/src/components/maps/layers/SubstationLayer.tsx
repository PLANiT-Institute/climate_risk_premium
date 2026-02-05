import { CircleMarker, Popup } from "react-leaflet";
import type { Feature, Point } from "geojson";
import { ASSET_COLORS } from "@/lib/geo/hazard-colors";
import type { SubstationProperties } from "@/lib/geo/types";

interface SubstationLayerProps {
  feature: Feature<Point, SubstationProperties>;
}

export default function SubstationLayer({ feature }: SubstationLayerProps) {
  const coords = feature.geometry.coordinates;
  const position: [number, number] = [coords[1], coords[0]];
  const props = feature.properties;

  return (
    <CircleMarker
      center={position}
      radius={10}
      pathOptions={{
        fillColor: ASSET_COLORS.substation,
        fillOpacity: 0.8,
        color: "#333",
        weight: 2,
      }}
    >
      <Popup>
        <div className="min-w-[150px]">
          <h3 className="font-bold text-base mb-2">{props.name}</h3>
          <table className="text-sm w-full">
            <tbody>
              <tr>
                <td className="text-slate-500 pr-3">Type:</td>
                <td className="font-medium capitalize">{props.type}</td>
              </tr>
              <tr>
                <td className="text-slate-500 pr-3">Location:</td>
                <td className="font-mono text-xs">
                  {coords[1].toFixed(3)}°N, {coords[0].toFixed(3)}°E
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Popup>
    </CircleMarker>
  );
}
