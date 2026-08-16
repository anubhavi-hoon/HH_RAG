import { Section } from "./Section";
import type { Language } from "../types/rag";

interface AnswerPanelProps {
  answer: string;
  grounded: boolean;
  confidence: number;
  language: Language;
}

export function AnswerPanel({ answer, grounded, confidence, language }: AnswerPanelProps) {
  const percent = Math.round(Math.max(0, Math.min(1, confidence)) * 100);

  return (
    <Section
      label="Answer"
      aside={
        <div className="flex flex-wrap items-center gap-2 text-[11px]">
          <span
            className={[
              "rounded border px-2 py-0.5 font-mono uppercase tracking-wide",
              grounded
                ? "border-emerald-900 text-emerald-300"
                : "border-amber-900 text-amber-300",
            ].join(" ")}
          >
            <span aria-hidden="true" className="mr-1">
              {grounded ? "✓" : "!"}
            </span>
            {grounded ? "Grounded" : "Not grounded"}
          </span>
          <span className="rounded border border-zinc-800 px-2 py-0.5 font-mono text-zinc-400">
            Confidence {percent}%
          </span>
        </div>
      }
    >
      <p
        lang={language}
        className="max-w-3xl text-xl leading-relaxed text-zinc-100 sm:text-2xl"
      >
        {answer}
      </p>

      <div className="mt-5 max-w-xs">
        <div
          className="h-1 w-full overflow-hidden rounded-full bg-zinc-900"
          role="meter"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Answer confidence"
        >
          <div
            className={grounded ? "h-full bg-emerald-500/70" : "h-full bg-amber-500/70"}
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>
    </Section>
  );
}
