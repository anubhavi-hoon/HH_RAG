import { EmptyState, Section } from "./Section";
import type { Source } from "../types/rag";

interface SourcesPanelProps {
  sources: Source[];
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-[10px] uppercase tracking-[0.14em] text-zinc-600">{label}</dt>
      <dd className="truncate font-mono text-xs text-zinc-300" title={value}>
        {value}
      </dd>
    </div>
  );
}

export function SourcesPanel({ sources }: SourcesPanelProps) {
  return (
    <Section
      label="Sources"
      aside={
        <span className="font-mono text-[11px] text-zinc-500">
          {sources.length} retrieved
        </span>
      }
    >
      {sources.length === 0 ? (
        <EmptyState>
          No sources were retrieved for this answer. The response is ungrounded and
          should not be treated as factual.
        </EmptyState>
      ) : (
        <ol className="space-y-3">
          {sources.map((source, index) => (
            <li
              key={source.chunk_id}
              className="rounded-md border border-zinc-900 bg-zinc-950/60 p-4"
            >
              <div className="mb-3 flex items-start justify-between gap-4">
                <span className="font-mono text-[11px] text-zinc-600">
                  [{index + 1}]
                </span>
                <span className="font-mono text-xs text-zinc-300">
                  {(source.score * 100).toFixed(1)}% relevance
                </span>
              </div>

              <dl className="mb-3 grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-4">
                <Meta label="Chunk ID" value={source.chunk_id} />
                <Meta label="Document" value={source.doc_id ?? "unavailable"} />
                <Meta
                  label="Language"
                  value={source.language === "hi" ? "hi · Hindi" : "en · English"}
                />
                <Meta label="Strategy" value={source.strategy ?? "unavailable"} />
              </dl>

              <p
                lang={source.language}
                className="border-l border-zinc-800 pl-3 text-sm leading-relaxed text-zinc-400"
              >
                {source.text}
              </p>
            </li>
          ))}
        </ol>
      )}
    </Section>
  );
}
