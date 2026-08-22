import { Check, Copy, Volume2, VolumeX } from "lucide-react";
import { useState } from "react";
import { FormattedAnswer } from "../FormattedAnswer";
import type { Language, Source } from "../../types/rag";

interface AnswerCardProps {
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

export function AnswerCard({
  answer,
  grounded,
  confidence,
  language,
  sources = [],
}: AnswerCardProps) {
  const [copied, setCopied] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const percent = Math.round(Math.max(0, Math.min(1, confidence)) * 100);
  const isRefusal = isRefusalAnswer(answer);
  const isGeneralKnowledge = !grounded && sources.length === 0 && !isRefusal;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  const handleToggleSpeak = () => {
    if (!("speechSynthesis" in window)) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(answer);
    utterance.lang = language === "hi" ? "hi-IN" : "en-US";
    utterance.rate = 1.0;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <section className="relative rounded-2xl border border-white/[0.08] bg-[#08090B] p-6 sm:p-8 shadow-xl transition-all">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] pb-4">
        <div className="flex items-center gap-3">
          <span className="text-xs uppercase tracking-widest text-zinc-400 font-medium">
            Answer
          </span>

          <div className="h-3 w-px bg-white/[0.08]" aria-hidden="true" />

          {/* Verification Status */}
          {grounded ? (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.12] bg-white/[0.04] px-2.5 py-0.5 text-xs text-zinc-200">
              <span className="text-white">✓</span> Grounded
            </span>
          ) : isGeneralKnowledge ? (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.02] px-2.5 py-0.5 text-xs text-zinc-400">
              General Knowledge
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.02] px-2.5 py-0.5 text-xs text-zinc-500">
              Ungrounded
            </span>
          )}

          <span className="text-xs text-zinc-500">
            {percent}% confidence
          </span>

          {sources.length > 0 && (
            <span className="text-xs text-zinc-500">
              · {sources.length} {sources.length === 1 ? "source" : "sources"}
            </span>
          )}
        </div>

        {/* Action Tools: Audio Speak & Copy */}
        <div className="flex items-center gap-1">
          {"speechSynthesis" in window && (
            <button
              type="button"
              onClick={handleToggleSpeak}
              aria-label={isSpeaking ? "Stop speaking" : "Speak answer"}
              title={isSpeaking ? "Stop speech" : "Read answer aloud"}
              className={`flex h-7 w-7 items-center justify-center rounded-lg text-zinc-400 transition-colors cursor-pointer ${
                isSpeaking ? "text-white bg-white/10" : "hover:text-white"
              }`}
            >
              {isSpeaking ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
            </button>
          )}

          <button
            type="button"
            onClick={handleCopy}
            aria-label="Copy answer to clipboard"
            title="Copy answer"
            className="flex h-7 w-7 items-center justify-center rounded-lg text-zinc-400 transition-colors hover:text-white cursor-pointer"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-white" /> : <Copy className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Main Answer Content Body */}
      <div className="mt-5 text-sm sm:text-base leading-relaxed text-[#F5F5F5]">
        <FormattedAnswer content={answer} language={language} />
      </div>
    </section>
  );
}
