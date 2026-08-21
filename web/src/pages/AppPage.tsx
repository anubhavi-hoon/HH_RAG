import { useCallback, useEffect, useRef, useState } from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

import { RagApiError, checkHealth, queryRag, voiceRag } from "../api/rag";
import { useVoiceRecorder } from "../hooks/useVoiceRecorder";
import { AppHeader } from "../components/workspace/AppHeader";
import { FuturisticVoiceCore } from "../components/workspace/FuturisticVoiceCore";
import { QuestionComposer } from "../components/workspace/QuestionComposer";
import { QuickPrompts } from "../components/workspace/QuickPrompts";
import { TranscriptBanner } from "../components/workspace/TranscriptBanner";
import { AnswerCard } from "../components/workspace/AnswerCard";
import { EvidenceDossier } from "../components/workspace/EvidenceDossier";
import { PerformanceTelemetry } from "../components/workspace/PerformanceTelemetry";
import type { BackendStatus, InteractionState, RagResult } from "../types/rag";

const HEALTH_POLL_MS = 20_000;

function toFriendlyMessage(error: unknown): string {
  if (error instanceof RagApiError) return error.message;
  return "Could not complete the request. Please check the backend connection or try again.";
}

interface AppPageProps {
  onNavigateHome?: () => void;
}

export function AppPage({ onNavigateHome }: AppPageProps) {
  const [interaction, setInteraction] = useState<InteractionState>("idle");
  const [result, setResult] = useState<RagResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [textQuery, setTextQuery] = useState("");
  const [selectedLang, setSelectedLang] = useState<"auto" | "en" | "hi">("auto");
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");
  const [serviceName, setServiceName] = useState<string | null>(null);
  const inFlight = useRef(false);

  // Health check polling
  useEffect(() => {
    let cancelled = false;

    const ping = async () => {
      try {
        const health = await checkHealth();
        if (cancelled) return;
        setBackendStatus(health.status === "ok" ? "online" : "offline");
        setServiceName(health.service);
      } catch {
        if (!cancelled) {
          setBackendStatus("offline");
          setServiceName(null);
        }
      }
    };

    void ping();
    const timer = window.setInterval(ping, HEALTH_POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const runRequest = useCallback(async (call: () => Promise<RagResult>) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setInteraction("processing");
    setErrorMessage(null);
    try {
      const outcome = await call();
      setResult(outcome);
      setInteraction("complete");
    } catch (error) {
      setErrorMessage(toFriendlyMessage(error));
      setInteraction("error");
    } finally {
      inFlight.current = false;
    }
  }, []);

  const handleRecordingComplete = useCallback(
    (audio: Blob) => {
      void runRequest(() => voiceRag(audio));
    },
    [runRequest],
  );

  const handleRecordingError = useCallback((message: string) => {
    setErrorMessage(message);
    setInteraction("error");
  }, []);

  const recorder = useVoiceRecorder({
    onComplete: handleRecordingComplete,
    onError: handleRecordingError,
  });

  const handleToggleRecording = useCallback(async () => {
    if (interaction === "recording") {
      setInteraction("processing");
      recorder.stop();
      return;
    }
    setErrorMessage(null);
    const started = await recorder.start();
    if (started) {
      setInteraction("recording");
    }
  }, [interaction, recorder]);

  const handleTextSubmit = useCallback(() => {
    const trimmed = textQuery.trim();
    if (!trimmed) {
      setErrorMessage("Please enter a question before sending.");
      setInteraction("error");
      return;
    }
    void runRequest(() => queryRag(trimmed));
  }, [runRequest, textQuery]);

  const handlePromptSelect = useCallback(
    (promptText: string) => {
      setTextQuery(promptText);
      void runRequest(() => queryRag(promptText));
    },
    [runRequest],
  );

  const handleReset = () => {
    setResult(null);
    setTextQuery("");
    setErrorMessage(null);
    setInteraction("idle");
  };

  const handleNavigateHome = () => {
    if (onNavigateHome) {
      onNavigateHome();
    } else {
      window.history.pushState({}, "", "/");
      window.dispatchEvent(new PopStateEvent("popstate"));
    }
  };

  const busy = interaction === "processing";

  return (
    <div className="relative min-h-screen bg-[#030405] text-[#F5F5F5] selection:bg-white/15 selection:text-white flex flex-col justify-between">
      {/* Top Header */}
      <AppHeader
        backendStatus={backendStatus}
        serviceName={serviceName}
        onNavigateHome={handleNavigateHome}
      />

      {/* Main Container */}
      <main className="relative mx-auto w-full max-w-4xl px-5 py-8 sm:py-12 flex-1 flex flex-col justify-center">
        {/* Error Alert */}
        {errorMessage && (
          <div
            role="alert"
            className="mb-8 flex items-center justify-between gap-3 rounded-xl border border-white/[0.10] bg-[#0C0E12] p-4 text-xs text-zinc-300 shadow-lg backdrop-blur-md"
          >
            <div className="flex items-center gap-2.5">
              <AlertCircle className="h-4 w-4 text-zinc-400 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              type="button"
              onClick={() => setErrorMessage(null)}
              className="text-zinc-500 hover:text-white text-xs cursor-pointer"
            >
              ✕
            </button>
          </div>
        )}

        {/* View Mode A: Quiet Minimal Hero View */}
        {!result ? (
          <div className="flex flex-col items-center gap-10 py-6 sm:py-10">
            {/* Main Hero Typography */}
            <div className="text-center space-y-3">
              <span className="text-[11px] font-medium tracking-[0.2em] text-zinc-500 uppercase">
                Multilingual Voice & Text
              </span>
              <h1 className="text-3xl sm:text-5xl font-semibold tracking-tight text-[#F5F5F5]">
                Ask Vaani anything.
              </h1>
              <p className="text-sm sm:text-base text-zinc-400 max-w-md mx-auto leading-relaxed">
                Speak naturally in English or Hindi, or type your question.
              </p>
            </div>

            {/* Focal Point: Centerpiece Microphone */}
            <FuturisticVoiceCore
              state={interaction}
              disabled={!recorder.isSupported}
              onToggle={() => void handleToggleRecording()}
            />

            {!recorder.isSupported && (
              <p className="text-xs text-zinc-500">
                Microphone unsupported in this browser. Please type below.
              </p>
            )}

            {/* Main Floating Question Composer */}
            <QuestionComposer
              query={textQuery}
              onChange={setTextQuery}
              onSubmit={handleTextSubmit}
              onToggleVoice={() => void handleToggleRecording()}
              isRecording={interaction === "recording"}
              busy={busy}
              selectedLang={selectedLang}
              onSelectLang={setSelectedLang}
            />

            {/* Subtle Example Prompts */}
            <QuickPrompts onSelect={handlePromptSelect} disabled={busy || interaction === "recording"} />
          </div>
        ) : (
          /* View Mode B: Focused Response Experience */
          <div className="space-y-6 animate-in fade-in duration-400">
            {/* Top Back Action */}
            <div className="flex items-center justify-between pb-2">
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.02] px-3 py-1.5 text-xs text-zinc-400 transition-all hover:border-white/20 hover:bg-white/[0.06] hover:text-white cursor-pointer"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>New question</span>
              </button>
            </div>

            {/* Query Card */}
            <TranscriptBanner
              transcript={result.response.transcript}
              query={result.response.query}
              language={result.response.language}
            />

            {/* Verified Answer */}
            <AnswerCard
              answer={result.response.answer}
              grounded={result.response.grounded}
              confidence={result.response.confidence}
              language={result.response.language}
              sources={result.response.sources}
            />

            {/* Sources Dossier */}
            <EvidenceDossier sources={result.response.sources} />

            {/* Collapsible System Details & Latency */}
            <PerformanceTelemetry
              latency={result.response.latency}
              clientTotalMs={result.clientTotalMs}
            />

            {/* Follow-up Composer at Bottom */}
            <div className="pt-8 border-t border-white/[0.06]">
              <QuestionComposer
                query={textQuery}
                onChange={setTextQuery}
                onSubmit={handleTextSubmit}
                onToggleVoice={() => void handleToggleRecording()}
                isRecording={interaction === "recording"}
                busy={busy}
                selectedLang={selectedLang}
                onSelectLang={setSelectedLang}
              />
            </div>
          </div>
        )}
      </main>

      {/* Subtle Minimal Footer */}
      <footer className="border-t border-white/[0.04] py-6 px-5 text-center text-xs text-zinc-600">
        VAANI · वाणी
      </footer>
    </div>
  );
}
