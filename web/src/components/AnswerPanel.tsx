import { Section } from "./Section";
import { FormattedAnswer } from "./FormattedAnswer";
import type { Language, Source } from "../types/rag";

interface AnswerPanelProps {
  answer: string;
  grounded: boolean;
  confidence: number;
  language: Language;
  sources?: Source[];
}

function isRefusalAnswer(text: string): boolean {
  const lower = text.toLowerCase();
  return (
    lower.includes("does not contain sufficient support") ||
    lower.includes("available context is insufficient") ||
    lower.includes("available knowledge context is insufficient") ||
    lower.includes("could not find a grounded answer") ||
    lower.includes("insufficient context") ||
    lower.includes("अनुक्रमित अनुच्छेदों में नहीं मिला")
  );
}

export function AnswerPanel({
  answer,
  grounded,
  confidence,
  language,
  sources = [],
}: AnswerPanelProps) {
  const percent = Math.round(Math.max(0, Math.min(1, confidence)) * 100);
  const isRefusal = isRefusalAnswer(answer);
  const isGeneralKnowledge = !grounded && sources.length === 0 && !isRefusal;

  return (
    <Section
      label="Answer"
      aside={
        <div className="flex flex-wrap items-center gap-2 text-[11px]">
          {isGeneralKnowledge ? (
            <span className="rounded border border-zinc-800 bg-zinc-900/60 px-2 py-0.5 font-mono uppercase tracking-wide text-zinc-300">
              <span aria-hidden="true" className="mr-1 text-zinc-400">
                ✦
              </span>
              General knowledge
            </span>
          ) : (
            <>
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
            </>
          )}
        </div>
      }
    >
      <FormattedAnswer content={answer} language={language} />

      {!isGeneralKnowledge && (
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
      )}
    </Section>
  );
}
