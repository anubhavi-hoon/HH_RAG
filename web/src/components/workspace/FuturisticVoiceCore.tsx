import { Mic, Square, Loader2 } from "lucide-react";
import type { InteractionState } from "../../types/rag";

interface FuturisticVoiceCoreProps {
  state: InteractionState;
  disabled?: boolean;
  onToggle: () => void;
  compact?: boolean;
}

export function FuturisticVoiceCore({
  state,
  disabled = false,
  onToggle,
  compact = false,
}: FuturisticVoiceCoreProps) {
  const isRecording = state === "recording";
  const isProcessing = state === "processing";

  const getStatusText = () => {
    switch (state) {
      case "recording":
        return { label: "Listening...", sub: "Click to finish speaking" };
      case "processing":
        return { label: "Thinking...", sub: "Retrieving & synthesizing" };
      case "complete":
        return { label: "Answer ready", sub: "Click to ask another" };
      case "error":
        return { label: "Something went wrong", sub: "Click to try again" };
      default:
        return { label: "Speak your question", sub: "Ready" };
    }
  };

  const status = getStatusText();

  return (
    <div className={`relative flex flex-col items-center justify-center transition-all duration-500 ${compact ? "py-2" : "py-6"}`}>
      {/* Barely visible ambient light */}
      <div
        className={`pointer-events-none absolute h-52 w-52 rounded-full bg-white/[0.02] blur-3xl transition-opacity duration-700 ${
          isRecording ? "opacity-100 scale-110" : isProcessing ? "opacity-75" : "opacity-30"
        }`}
      />

      {/* Main Microphone Orb (180-220px desktop) */}
      <div className={`relative flex items-center justify-center ${compact ? "h-24 w-24" : "h-48 w-48 sm:h-52 sm:w-52"}`}>
        {/* Outer Ring */}
        <div
          className={`pointer-events-none absolute inset-0 rounded-full border transition-all duration-500 ${
            isRecording
              ? "border-white/30 animate-pulse-gently"
              : isProcessing
              ? "border-white/20 animate-rotate-slow border-t-white/50"
              : "border-white/[0.12] animate-orb-breathe"
          }`}
        />

        {/* Inner Surface & Action Button */}
        <button
          type="button"
          onClick={onToggle}
          disabled={disabled || isProcessing}
          aria-label={
            isRecording
              ? "Stop recording"
              : isProcessing
              ? "Processing query"
              : "Speak your question"
          }
          className={`group relative z-10 flex items-center justify-center rounded-full border border-white/[0.08] bg-[#08090B] shadow-2xl transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40 focus-visible:ring-offset-4 focus-visible:ring-offset-black disabled:cursor-not-allowed ${
            compact ? "h-20 w-20" : "h-40 w-40 sm:h-44 sm:w-44"
          } ${
            isRecording
              ? "border-white/40 bg-white/[0.06] shadow-[0_0_40px_rgba(255,255,255,0.08)] scale-102"
              : isProcessing
              ? "border-white/20 cursor-wait"
              : "hover:border-white/30 hover:bg-white/[0.03] hover:scale-[1.02] cursor-pointer"
          }`}
        >
          {isProcessing ? (
            <Loader2 className={`animate-spin text-white ${compact ? "h-6 w-6" : "h-8 w-8 sm:h-9 sm:w-9"}`} />
          ) : isRecording ? (
            <Square className={`text-white fill-white transition-transform group-hover:scale-105 ${compact ? "h-5 w-5" : "h-7 w-7 sm:h-8 sm:w-8"}`} />
          ) : (
            <Mic className={`text-[#F5F5F5] transition-transform duration-300 group-hover:scale-105 ${compact ? "h-6 w-6" : "h-8 w-8 sm:h-10 sm:w-10"}`} />
          )}
        </button>
      </div>

      {/* State & Feedback Labels */}
      {!compact && (
        <div className="mt-5 flex flex-col items-center gap-1 text-center select-none">
          <p className="text-sm font-medium text-white tracking-tight">
            {status.label}
          </p>
          <p className="text-xs text-zinc-500 font-normal">
            {status.sub}
          </p>
        </div>
      )}
    </div>
  );
}
