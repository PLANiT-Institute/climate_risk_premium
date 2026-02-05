import { GeoJSON, Popup } from "react-leaflet";
import type { Feature, Polygon } from "geojson";
import type { PathOptions } from "leaflet";
import { ASSET_COLORS } from "@/lib/geo/hazard-colors";
import type { PowerPlantProperties } from "@/lib/geo/types";

interface PowerPlantLayerProps {
  feature: Feature<Polygon, PowerPlantProperties>;
}

export default function PowerPlantLayer({ feature }: PowerPlantLayerProps) {
  const style: PathOptions = {
    fillColor: ASSET_COLORS.powerPlant,
    fillOpacity: 0.4,
    color: "#8e1b1b",
    weight: 2,
  };

  const props = feature.properties;

  return (
    <GeoJSON data={feature} style={style}>
      <Popup>
        <div className="min-w-[200px]">
          <h3 className="font-bold text-base mb-2">{props.name}</h3>
          <table className="text-sm w-full">
            <tbody>
              <tr>
                <td className="text-slate-500 pr-3">Capacity:</td>
                <td className="font-medium">{props.capacity_mw}</td>
              </tr>
              <tr>
                <td className="text-slate-500 pr-3">Fuel:</td>
                <td className="font-medium capitalize">{props.source}</td>
              </tr>
              <tr>
                <td className="text-slate-500 pr-3">Type:</td>
                <td className="font-medium capitalize">{props.method}</td>
              </tr>
              <tr>
                <td className="text-slate-500 pr-3">Location:</td>
                <td className="font-mono text-xs">
                  {props.center_lat?.toFixed(3)}°N, {props.center_lon?.toFixed(3)}°E
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Popup>
    </GeoJSON>
  );
}
