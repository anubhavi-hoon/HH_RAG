import { Section } from "./Section";
import type { Language } from "../types/rag";

interface TranscriptPanelProps {
  transcript: string | null;
  query: string;
  language: Language;
}

export function TranscriptPanel({ transcript, query, language }: TranscriptPanelProps) {
  const spoken = Boolean(transcript);
  const text = transcript ?? query;

  return (
    <Section
      label="Transcript"
      aside={
        <div className="flex items-center gap-2 font-mono text-[11px] text-zinc-500">
          <span className="rounded border border-zinc-800 px-2 py-0.5 uppercase">
            {language === "hi" ? "hi · Hindi" : "en · English"}
          </span>
          <span className="rounded border border-zinc-800 px-2 py-0.5">
            {spoken ? "voice" : "typed"}
          </span>
        </div>
      }
    >
      <p lang={language} className="text-lg leading-relaxed text-zinc-200">
        {text}
      </p>
    </Section>
  );
}
