import type { Language } from "../../types/rag";

interface TranscriptBannerProps {
  transcript: string | null;
  query: string;
  language: Language;
}

export function TranscriptBanner({ transcript, query, language }: TranscriptBannerProps) {
  const isSpoken = Boolean(transcript);
  const displayText = transcript ?? query;

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-[#08090B] p-6 sm:p-7 shadow-xl transition-all">
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 mb-3">
        <span className="text-xs uppercase tracking-widest text-zinc-500 font-medium">
          Query
        </span>

        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <span>{language === "hi" ? "हिन्दी" : "English"}</span>
          <span>·</span>
          <span>{isSpoken ? "Voice" : "Typed"}</span>
        </div>
      </div>

      <p
        lang={language}
        className="text-lg sm:text-xl font-medium text-white tracking-tight leading-relaxed"
      >
        &ldquo;{displayText}&rdquo;
      </p>
    </div>
  );
}
