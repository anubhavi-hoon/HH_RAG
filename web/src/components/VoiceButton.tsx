import type { InteractionState } from "../types/rag";

interface VoiceButtonProps {
  state: InteractionState;
  disabled?: boolean;
  onToggle: () => void;
}

const STATE_STYLE: Record<InteractionState, string> = {
  idle: "border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:text-white",
  recording: "border-rose-500 text-rose-300",
  processing: "border-amber-400/70 text-amber-200",
  complete: "border-emerald-500/70 text-emerald-200",
  error: "border-rose-600 text-rose-300",
};

const STATE_LABEL: Record<InteractionState, string> = {
  idle: "Speak your question",
  recording: "Recording — click to stop",
  processing: "Processing your question",
  complete: "Answer ready — ask another",
  error: "Something went wrong — try again",
};

const ARIA_LABEL: Record<InteractionState, string> = {
  idle: "Start recording your question",
  recording: "Stop recording and send the question",
  processing: "Processing, please wait",
  complete: "Start a new recording",
  error: "Retry recording",
};

function MicIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-9 w-9"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="9" y="2.5" width="6" height="11" rx="3" />
      <path d="M5.5 11a6.5 6.5 0 0 0 13 0" />
      <path d="M12 17.5V21" />
      <path d="M8.5 21h7" />
    </svg>
  );
}

function StopIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-8 w-8" fill="currentColor" aria-hidden="true">
      <rect x="7" y="7" width="10" height="10" rx="2" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-8 w-8 animate-spin"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="9" className="opacity-25" />
      <path d="M21 12a9 9 0 0 0-9-9" strokeLinecap="round" />
    </svg>
  );
}

export function VoiceButton({ state, disabled, onToggle }: VoiceButtonProps) {
  const isProcessing = state === "processing";
  const isRecording = state === "recording";

  return (
    <div className="flex flex-col items-center gap-4">
      <button
        type="button"
        onClick={onToggle}
        disabled={disabled || isProcessing}
        aria-label={ARIA_LABEL[state]}
        aria-pressed={isRecording}
        aria-busy={isProcessing}
        className={[
          "relative flex h-28 w-28 items-center justify-center rounded-full border transition-colors duration-200",
          "bg-zinc-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-200 focus-visible:ring-offset-4 focus-visible:ring-offset-black",
          "disabled:cursor-not-allowed disabled:opacity-60",
          STATE_STYLE[state],
        ].join(" ")}
      >
        {isRecording ? (
          <span
            className="absolute inset-0 animate-ping rounded-full border border-rose-500/40"
            aria-hidden="true"
          />
        ) : null}
        {isProcessing ? <Spinner /> : isRecording ? <StopIcon /> : <MicIcon />}
      </button>

      <p className="text-sm text-zinc-400" aria-live="polite">
        {STATE_LABEL[state]}
      </p>
    </div>
  );
}
