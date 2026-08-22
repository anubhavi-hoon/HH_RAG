import { ChevronDown } from "lucide-react";
import { useState } from "react";
import type { Source } from "../../types/rag";

interface EvidenceDossierProps {
  sources: Source[];
}

export function EvidenceDossier({ sources }: EvidenceDossierProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!sources || sources.length === 0) {
    return null;
  }

  const toggleExpand = (index: number) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  return (
    <section className="rounded-2xl border border-white/[0.08] bg-[#08090B] p-6 sm:p-8 shadow-xl transition-all">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
        <span className="text-xs uppercase tracking-widest text-zinc-400 font-medium">
          Sources ({sources.length})
        </span>
        <span className="text-xs text-zinc-500">
          Retrieved evidence
        </span>
      </div>

      {/* Sources List */}
      <div className="mt-4 space-y-2.5">
        {sources.map((source, index) => {
          const isExpanded = expandedIndex === index;
          const relevancePercent = (source.score * 100).toFixed(0);

          return (
            <div
              key={source.chunk_id || index}
              className="rounded-xl border border-white/[0.06] bg-[#0D0F12] p-4 transition-all hover:border-white/15"
            >
              {/* Header Row */}
              <div
                onClick={() => toggleExpand(index)}
                className="flex items-center justify-between gap-3 cursor-pointer select-none"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="text-xs font-medium text-white">
                    Source {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="text-xs text-zinc-500 truncate">
                    {source.doc_id ? `· doc_${source.doc_id}` : ""}
                  </span>
                </div>

                <div className="flex items-center gap-2.5 shrink-0 text-xs text-zinc-400">
                  <span>{relevancePercent}% relevance</span>
                  <ChevronDown
                    className={`h-3.5 w-3.5 text-zinc-500 transition-transform duration-200 ${
                      isExpanded ? "rotate-180 text-white" : ""
                    }`}
                  />
                </div>
              </div>

              {/* Passage Content */}
              <div className="mt-2.5 border-l border-white/[0.08] pl-3">
                <p
                  lang={source.language}
                  className={`text-xs leading-relaxed text-zinc-300 ${
                    !isExpanded ? "line-clamp-2" : ""
                  }`}
                >
                  &ldquo;{source.text}&rdquo;
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
