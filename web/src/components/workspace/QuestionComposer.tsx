import { ArrowUp, Mic, X } from "lucide-react";
import { useRef } from "react";

interface QuestionComposerProps {
  query: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onToggleVoice: () => void;
  isRecording: boolean;
  busy: boolean;
  selectedLang: "auto" | "en" | "hi";
  onSelectLang: (lang: "auto" | "en" | "hi") => void;
}

export function QuestionComposer({
  query,
  onChange,
  onSubmit,
  onToggleVoice,
  isRecording,
  busy,
  selectedLang,
  onSelectLang,
}: QuestionComposerProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!busy && query.trim()) {
        onSubmit();
      }
    }
  };

  return (
    <div className="relative mx-auto w-full max-w-[640px]">
      <div
        className={`relative flex items-center h-14 sm:h-16 rounded-[18px] border bg-[#090A0C] px-4 shadow-xl transition-all duration-300 ${
          busy
            ? "border-white/20 opacity-80"
            : isRecording
            ? "border-white/30 shadow-[0_0_30px_rgba(255,255,255,0.06)]"
            : "border-white/[0.10] focus-within:border-white/30 hover:border-white/20"
        }`}
      >
        {/* Input Field */}
        <input
          ref={inputRef}
          type="text"
          id="workspace-query-input"
          value={query}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything in English or Hindi..."
          autoComplete="off"
          disabled={busy || isRecording}
          className="w-full bg-transparent text-sm sm:text-base text-[#F5F5F5] placeholder:text-zinc-500 focus:outline-none disabled:opacity-50 font-normal"
        />

        {query && !busy && (
          <button
            type="button"
            onClick={() => onChange("")}
            aria-label="Clear text"
            className="mr-2 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-zinc-500 hover:text-zinc-200 transition-colors cursor-pointer"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}

        {/* Right Actions: Mic & Submit */}
        <div className="flex items-center gap-1.5 shrink-0 pl-1">
          <button
            type="button"
            onClick={onToggleVoice}
            disabled={busy}
            aria-label={isRecording ? "Stop recording" : "Record question"}
            className={`flex h-9 w-9 items-center justify-center rounded-full text-zinc-400 transition-colors cursor-pointer ${
              isRecording
                ? "bg-white/20 text-white animate-pulse"
                : "hover:bg-white/[0.06] hover:text-white"
            }`}
          >
            <Mic className="h-4 w-4" />
          </button>

          <button
            type="button"
            onClick={onSubmit}
            disabled={busy || !query.trim() || isRecording}
            aria-label="Ask Vaani"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-black transition-all hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-30 cursor-pointer shadow-sm"
          >
            <ArrowUp className="h-4 w-4 stroke-[2.5]" />
          </button>
        </div>
      </div>

      {/* Subtle Language Indicator below composer */}
      <div className="mt-2.5 flex items-center justify-center gap-2 text-xs text-zinc-500 select-none">
        <button
          type="button"
          onClick={() => onSelectLang("auto")}
          className={`transition-colors cursor-pointer ${selectedLang === "auto" ? "text-zinc-300 font-medium" : "hover:text-zinc-400"}`}
        >
          AUTO
        </button>
        <span>·</span>
        <button
          type="button"
          onClick={() => onSelectLang("en")}
          className={`transition-colors cursor-pointer ${selectedLang === "en" ? "text-zinc-300 font-medium" : "hover:text-zinc-400"}`}
        >
          EN
        </button>
        <span>·</span>
        <button
          type="button"
          onClick={() => onSelectLang("hi")}
          className={`font-['Noto_Sans_Devanagari'] transition-colors cursor-pointer ${selectedLang === "hi" ? "text-zinc-300 font-medium" : "hover:text-zinc-400"}`}
        >
          हिन्दी
        </button>
      </div>
    </div>
  );
}
