"use client";

import { useEffect, useRef } from "react";
import katex from "katex";

interface EquationBlockProps {
  latex: string;
  label?: string;
  displayMode?: boolean;
}

export default function EquationBlock({
  latex,
  label,
  displayMode = true,
}: EquationBlockProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      katex.render(latex, ref.current, {
        displayMode,
        throwOnError: false,
        trust: true,
      });
    }
  }, [latex, displayMode]);

  return (
    <div className="bg-slate-50 rounded-lg p-4 my-3">
      {label && (
        <p className="text-xs font-semibold text-slate-500 mb-2">{label}</p>
      )}
      <div ref={ref} className="overflow-x-auto" />
    </div>
  );
}
