import { Section } from "./Section";
import type { LatencyMetrics } from "../types/rag";

interface LatencyMetricsPanelProps {
  latency: LatencyMetrics;
  /** Round trip measured in the browser — the only user-facing latency. */
  clientTotalMs: number;
}

const STAGES: Array<{ key: keyof LatencyMetrics; label: string }> = [
  { key: "stt_ms", label: "STT" },
  { key: "embedding_ms", label: "Embedding" },
  { key: "retrieval_ms", label: "Retrieval" },
  { key: "generation_ms", label: "Generation" },
  { key: "guardrail_ms", label: "Guardrails" },
];

function formatMs(value: number): string {
  if (value >= 100) return `${value.toFixed(0)} ms`;
  if (value >= 1) return `${value.toFixed(1)} ms`;
  return `${value.toFixed(2)} ms`;
}

function Metric({
  label,
  value,
  hint,
  emphasis,
}: {
  label: string;
  value: number;
  hint: string;
  emphasis?: boolean;
}) {
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-[0.14em] text-zinc-600">{label}</dt>
      <dd
        className={
          emphasis
            ? "mt-1 font-mono text-lg font-medium text-white"
            : "mt-1 font-mono text-sm text-zinc-200"
        }
      >
        {value > 0 ? formatMs(value) : <span className="text-zinc-600">not measured</span>}
      </dd>
      <p className="mt-1 text-[10px] leading-tight text-zinc-700">{hint}</p>
    </div>
  );
}

export function LatencyMetricsPanel({ latency, clientTotalMs }: LatencyMetricsPanelProps) {
  return (
    <Section
      label="Performance"
      aside={
        <span className="font-mono text-xs text-zinc-300">
          Round trip {formatMs(clientTotalMs)}
        </span>
      }
    >
      <dl className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-4 lg:grid-cols-7">
        <Metric
          label="Round trip"
          value={clientTotalMs}
          hint="Measured in browser"
          emphasis
        />
        <Metric label="Server" value={latency.total_ms} hint="Service wall clock" />
        {STAGES.map(({ key, label }) => (
          <Metric key={key} label={label} value={latency[key]} hint="Stage duration" />
        ))}
      </dl>

      <p className="mt-5 max-w-3xl text-xs leading-relaxed text-zinc-600">
        Round trip is the end-to-end time this browser waited. Server is the
        backend&apos;s own wall-clock execution and is a subset of it. Stages read
        &ldquo;not measured&rdquo; until the real STT, retrieval and generation
        pipeline is wired in — no simulated values are shown.
      </p>
    </Section>
  );
}
