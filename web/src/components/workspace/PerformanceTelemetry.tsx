import { ChevronDown } from "lucide-react";
import { useState } from "react";
import type { LatencyMetrics } from "../../types/rag";

interface PerformanceTelemetryProps {
  latency: LatencyMetrics;
  clientTotalMs: number;
}

function formatMs(value: number): string {
  if (value >= 100) return `${value.toFixed(0)} ms`;
  if (value >= 1) return `${value.toFixed(1)} ms`;
  return `${value.toFixed(2)} ms`;
}

export function PerformanceTelemetry({ latency, clientTotalMs }: PerformanceTelemetryProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-2xl border border-white/[0.06] bg-[#08090B]/60 p-4 transition-all">
      {/* Trigger Bar */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between text-xs text-zinc-500 hover:text-zinc-300 transition-colors cursor-pointer select-none"
      >
        <span>System details & latency</span>
        <div className="flex items-center gap-2">
          <span>{formatMs(clientTotalMs)} total</span>
          <ChevronDown
            className={`h-3.5 w-3.5 transition-transform duration-200 ${
              open ? "rotate-180 text-white" : ""
            }`}
          />
        </div>
      </button>

      {/* Expanded Metrics Grid */}
      {open && (
        <div className="mt-4 border-t border-white/[0.04] pt-4 space-y-4 font-mono text-xs">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-lg border border-white/[0.04] bg-[#0D0F12] p-2.5">
              <span className="text-[10px] text-zinc-500 uppercase block">Round Trip</span>
              <span className="text-sm text-zinc-200 block mt-0.5">{formatMs(clientTotalMs)}</span>
            </div>

            <div className="rounded-lg border border-white/[0.04] bg-[#0D0F12] p-2.5">
              <span className="text-[10px] text-zinc-500 uppercase block">Server Total</span>
              <span className="text-sm text-zinc-200 block mt-0.5">
                {latency.total_ms > 0 ? formatMs(latency.total_ms) : "< 1 ms"}
              </span>
            </div>

            <div className="rounded-lg border border-white/[0.04] bg-[#0D0F12] p-2.5">
              <span className="text-[10px] text-zinc-500 uppercase block">Retrieval</span>
              <span className="text-sm text-zinc-200 block mt-0.5">
                {latency.retrieval_ms > 0 ? formatMs(latency.retrieval_ms) : "cached"}
              </span>
            </div>

            <div className="rounded-lg border border-white/[0.04] bg-[#0D0F12] p-2.5">
              <span className="text-[10px] text-zinc-500 uppercase block">Generation</span>
              <span className="text-sm text-zinc-200 block mt-0.5">
                {latency.generation_ms > 0 ? formatMs(latency.generation_ms) : "extractive"}
              </span>
            </div>
          </div>

          <div className="text-[11px] text-zinc-500 flex flex-wrap gap-x-4 gap-y-1">
            <span>• Embeddings: 384D all-MiniLM-L6-v2</span>
            <span>• Index: FAISS IndexFlatIP</span>
            <span>• STT: Sarvam AI saaras:v3</span>
            <span>• Guardrails: Active</span>
          </div>
        </div>
      )}
    </div>
  );
}
