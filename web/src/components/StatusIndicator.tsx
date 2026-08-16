import type { BackendStatus } from "../types/rag";

const STATUS_COPY: Record<BackendStatus, { label: string; dot: string; text: string }> = {
  checking: {
    label: "Checking backend",
    dot: "bg-amber-400",
    text: "text-amber-300",
  },
  online: {
    label: "Backend online",
    dot: "bg-emerald-400",
    text: "text-emerald-300",
  },
  offline: {
    label: "Backend offline",
    dot: "bg-rose-500",
    text: "text-rose-300",
  },
};

interface StatusIndicatorProps {
  status: BackendStatus;
  service?: string | null;
}

export function StatusIndicator({ status, service }: StatusIndicatorProps) {
  const copy = STATUS_COPY[status];

  return (
    <div
      className="flex items-center gap-2 rounded-full border border-zinc-800 px-3 py-1.5"
      role="status"
      aria-live="polite"
      aria-label={copy.label}
      title={copy.label}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${copy.dot}`} aria-hidden="true" />
      <span className={`text-xs font-medium ${copy.text}`}>{copy.label}</span>
      {service ? (
        <span className="hidden font-mono text-[10px] text-zinc-600 sm:inline">
          {service}
        </span>
      ) : null}
    </div>
  );
}
