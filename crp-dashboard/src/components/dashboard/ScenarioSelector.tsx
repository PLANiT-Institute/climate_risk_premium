"use client";

import { SCENARIO_LABELS } from "@/lib/constants";

interface ScenarioSelectorProps {
  selected: string[];
  onChange: (scenarios: string[]) => void;
  multiple?: boolean;
}

export default function ScenarioSelector({
  selected,
  onChange,
  multiple = false,
}: ScenarioSelectorProps) {
  const scenarios = Object.entries(SCENARIO_LABELS);

  if (!multiple) {
    return (
      <select
        className="border border-slate-300 rounded-md px-3 py-2 text-sm bg-white"
        value={selected[0] || "baseline"}
        onChange={(e) => onChange([e.target.value])}
      >
        {scenarios.map(([key, label]) => (
          <option key={key} value={key}>
            {label}
          </option>
        ))}
      </select>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {scenarios.map(([key, label]) => {
        const isSelected = selected.includes(key);
        return (
          <button
            key={key}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              isSelected
                ? "bg-teal-600 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
            onClick={() => {
              if (isSelected) {
                onChange(selected.filter((s) => s !== key));
              } else {
                onChange([...selected, key]);
              }
            }}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
