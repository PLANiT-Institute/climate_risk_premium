import { GeoJSON, Popup } from "react-leaflet";
import type { Feature, LineString } from "geojson";
import type { PathOptions } from "leaflet";
import { ASSET_COLORS } from "@/lib/geo/hazard-colors";
import type { TransmissionLineProperties } from "@/lib/geo/types";

interface TransmissionLayerProps {
  feature: Feature<LineString, TransmissionLineProperties>;
  lineType: "765kV" | "route";
}

export default function TransmissionLayer({ feature, lineType }: TransmissionLayerProps) {
  const is765kV = lineType === "765kV";

  const style: PathOptions = is765kV
    ? {
        color: ASSET_COLORS.transmission765kV,
        weight: 3,
        opacity: 0.8,
      }
    : {
        color: ASSET_COLORS.transmissionRoute,
        weight: 2,
        opacity: 0.7,
        dashArray: "8, 8",
      };

  const props = feature.properties;

  return (
    <GeoJSON data={feature} style={style}>
      <Popup>
        <div className="min-w-[180px]">
          <h3 className="font-bold text-base mb-2">
            {props.name || props.description || "Transmission Line"}
          </h3>
          <table className="text-sm w-full">
            <tbody>
              {props.voltage_kv && (
                <tr>
                  <td className="text-slate-500 pr-3">Voltage:</td>
                  <td className="font-medium">{props.voltage_kv} kV</td>
                </tr>
              )}
              {props.circuits && (
                <tr>
                  <td className="text-slate-500 pr-3">Circuits:</td>
                  <td className="font-medium">{props.circuits}</td>
                </tr>
              )}
              {props.cables && (
                <tr>
                  <td className="text-slate-500 pr-3">Cables:</td>
                  <td className="font-medium">{props.cables}</td>
                </tr>
              )}
              {props.from && (
                <tr>
                  <td className="text-slate-500 pr-3">From:</td>
                  <td className="font-medium">{props.from}</td>
                </tr>
              )}
              {props.to && (
                <tr>
                  <td className="text-slate-500 pr-3">To:</td>
                  <td className="font-medium">{props.to}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Popup>
    </GeoJSON>
  );
}
