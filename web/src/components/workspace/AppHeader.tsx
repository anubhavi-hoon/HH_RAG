import { ArrowLeft, HelpCircle } from "lucide-react";
import { useState } from "react";
import type { BackendStatus } from "../../types/rag";

interface AppHeaderProps {
  backendStatus: BackendStatus;
  serviceName: string | null;
  onNavigateHome: () => void;
}

export function AppHeader({ backendStatus, onNavigateHome }: AppHeaderProps) {
  const [showInfo, setShowInfo] = useState(false);

  const isOnline = backendStatus === "online";
  const isChecking = backendStatus === "checking";

  return (
    <>
      <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-white/[0.06] bg-[#030405]/90 px-5 sm:px-8 backdrop-blur-xl transition-all">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between">
          {/* Left: Brand & Navigation */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onNavigateHome}
              aria-label="Return to overview"
              className="group flex items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.02] px-2.5 py-1.5 text-xs text-zinc-400 transition-all hover:border-white/20 hover:bg-white/[0.06] hover:text-white cursor-pointer"
            >
              <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-0.5" />
              <span className="hidden sm:inline">Overview</span>
            </button>

            <div className="h-4 w-px bg-white/[0.08]" aria-hidden="true" />

            <div className="flex items-baseline gap-2">
              <span className="text-sm font-semibold tracking-tight text-white sm:text-base">
                VAANI
              </span>
              <span className="font-['Noto_Sans_Devanagari'] text-xs text-zinc-400">
                वाणी
              </span>
              <span className="hidden sm:inline text-xs text-zinc-500 font-normal">
                · Knowledge Workspace
              </span>
            </div>
          </div>

          {/* Right: Online Status & Language & Help */}
          <div className="flex items-center gap-3">
            {/* Status Pill */}
            <div className="flex items-center gap-2 text-xs text-zinc-400">
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isOnline
                    ? "bg-white shadow-[0_0_8px_rgba(255,255,255,0.8)]"
                    : isChecking
                    ? "bg-zinc-500 animate-pulse"
                    : "bg-zinc-600"
                }`}
              />
              <span className="text-zinc-300">
                {isOnline ? "Online" : isChecking ? "Connecting..." : "Offline"}
              </span>
            </div>

            <div className="h-3.5 w-px bg-white/[0.08]" aria-hidden="true" />

            {/* Language */}
            <div className="text-xs text-zinc-400 flex items-center gap-1">
              <span>EN</span>
              <span className="text-zinc-600">/</span>
              <span className="font-['Noto_Sans_Devanagari']">हिन्दी</span>
            </div>

            {/* Help */}
            <button
              type="button"
              onClick={() => setShowInfo(true)}
              aria-label="Workspace Information"
              className="flex h-7 w-7 items-center justify-center rounded-lg text-zinc-400 transition-colors hover:text-white cursor-pointer"
            >
              <HelpCircle className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Clean Info Dialog */}
      {showInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md">
          <div className="relative w-full max-w-md rounded-2xl border border-white/[0.10] bg-[#08090B] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
              <h2 className="text-sm font-medium text-white">
                About Vaani (वाणी)
              </h2>
              <button
                type="button"
                onClick={() => setShowInfo(false)}
                className="text-xs text-zinc-400 hover:text-white cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="mt-4 space-y-3 text-xs leading-relaxed text-zinc-300">
              <p>
                Vaani is a multilingual, voice-enabled AI knowledge assistant for English and Hindi.
              </p>
              <p className="text-zinc-400">
                You can ask questions by voice using your microphone or by typing in the composer. Responses are retrieved from indexed documents and verified against strict grounding guardrails.
              </p>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={() => setShowInfo(false)}
                className="rounded-lg bg-white px-4 py-1.5 text-xs font-semibold text-black hover:bg-zinc-200 transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
