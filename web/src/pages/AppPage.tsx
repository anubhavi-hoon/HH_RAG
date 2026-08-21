import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, Sparkles } from "lucide-react";

import { API_BASE_URL, RagApiError, checkHealth, queryRag, voiceRag } from "../api/rag";
import { useVoiceRecorder } from "../hooks/useVoiceRecorder";
import { AnswerPanel } from "../components/AnswerPanel";
import { LatencyMetricsPanel } from "../components/LatencyMetrics";
import { SourcesPanel } from "../components/SourcesPanel";
import { StatusIndicator } from "../components/StatusIndicator";
import { TranscriptPanel } from "../components/TranscriptPanel";
import { VoiceButton } from "../components/VoiceButton";
import type { BackendStatus, InteractionState, RagResult } from "../types/rag";

const HEALTH_POLL_MS = 20_000;

function toFriendlyMessage(error: unknown): string {
  if (error instanceof RagApiError) return error.message;
  return "Something went wrong while contacting the backend. Please try again.";
}

interface AppPageProps {
  onNavigateHome?: () => void;
}

export function AppPage({ onNavigateHome }: AppPageProps) {
  const [interaction, setInteraction] = useState<InteractionState>("idle");
  const [result, setResult] = useState<RagResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [textQuery, setTextQuery] = useState("");
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");
  const [serviceName, setServiceName] = useState<string | null>(null);
  const inFlight = useRef(false);

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
    if (started) setInteraction("recording");
  }, [interaction, recorder]);

  const handleTextSubmit = useCallback(
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const trimmed = textQuery.trim();
      if (!trimmed) {
        setErrorMessage("Enter a question before sending.");
        setInteraction("error");
        return;
      }
      void runRequest(() => queryRag(trimmed));
    },
    [runRequest, textQuery],
  );

  const handleBack = () => {
    if (onNavigateHome) {
      onNavigateHome();
    } else {
      window.history.pushState({}, "", "/");
      window.dispatchEvent(new PopStateEvent("popstate"));
    }
  };

  const busy = interaction === "processing";

  return (
    <div className="relative min-h-screen bg-[#030405] text-[#F5F5F5] selection:bg-white/15 selection:text-white">
      <div className="relative mx-auto w-full max-w-4xl px-5 py-6 sm:px-8 sm:py-10">
        {/* Top bar with back to home and status */}
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.08] pb-6 mb-8">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={handleBack}
              className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-3.5 py-1.5 text-xs font-medium text-zinc-300 transition-all hover:border-white/20 hover:bg-white/10 hover:text-white cursor-pointer"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Home</span>
            </button>

            <div className="flex items-baseline gap-2">
              <span className="font-semibold tracking-tight text-white sm:text-lg">
                VAANI
              </span>
              <span className="font-['Noto_Sans_Devanagari'] text-xs font-normal text-zinc-400">
                वाणी
              </span>
              <span className="hidden sm:inline text-xs text-zinc-500">
                · Knowledge Workspace
              </span>
            </div>
          </div>

          <StatusIndicator status={backendStatus} service={serviceName} />
        </header>

        <main className="space-y-8">
          {/* Voice & Query Section */}
          <div className="relative flex flex-col items-center gap-8 rounded-2xl border border-white/[0.08] bg-[#080A0E] p-8 sm:p-12 shadow-2xl">
            <div className="flex items-center gap-2 text-xs font-mono text-zinc-400 uppercase tracking-widest">
              <Sparkles className="h-3.5 w-3.5 text-zinc-400" />
              <span>Multilingual Voice & Text Query</span>
            </div>

            <VoiceButton
              state={interaction}
              disabled={!recorder.isSupported}
              onToggle={() => void handleToggleRecording()}
            />

            {!recorder.isSupported ? (
              <p className="text-xs text-zinc-400">
                This browser does not support microphone recording. Use the text input below.
              </p>
            ) : null}

            <form
              onSubmit={handleTextSubmit}
              className="relative flex w-full max-w-xl flex-col gap-3 sm:flex-row"
            >
              <label htmlFor="text-query" className="sr-only">
                Ask a question
              </label>
              <input
                id="text-query"
                type="text"
                value={textQuery}
                onChange={(event) => setTextQuery(event.target.value)}
                placeholder="Ask a question in English or Hindi (उदा. जलवायु परिवर्तन के क्या कारण हैं?)..."
                autoComplete="off"
                disabled={busy}
                className="flex-1 rounded-xl border border-white/[0.08] bg-[#05070A] px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus-visible:border-white/30 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white/20 disabled:opacity-60 transition-all shadow-inner"
              />
              <button
                type="submit"
                disabled={busy}
                className="rounded-xl bg-[#F2F2F2] px-6 py-3 text-sm font-semibold text-[#050505] transition-all hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-black disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer shadow-md"
              >
                {busy ? "Processing..." : "Ask Vaani"}
              </button>
            </form>
          </div>

          {errorMessage ? (
            <div
              role="alert"
              className="rounded-xl border border-rose-900/60 bg-rose-950/40 p-4 text-sm text-rose-200 backdrop-blur-md"
            >
              <span aria-hidden="true" className="mr-2 font-mono text-rose-400">
                ✕
              </span>
              {errorMessage}
            </div>
          ) : null}

          {result ? (
            <div className="space-y-6">
              <TranscriptPanel
                transcript={result.response.transcript}
                query={result.response.query}
                language={result.response.language}
              />
              <AnswerPanel
                answer={result.response.answer}
                grounded={result.response.grounded}
                confidence={result.response.confidence}
                language={result.response.language}
                sources={result.response.sources}
              />
              <SourcesPanel sources={result.response.sources} />
              <LatencyMetricsPanel
                latency={result.response.latency}
                clientTotalMs={result.clientTotalMs}
              />
            </div>
          ) : (
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.01] p-8 text-center">
              <p className="text-sm text-zinc-400">
                Ask any question by voice or text in English or Hindi to see the speech transcript, grounded answer, source verification, and stage-by-stage latency.
              </p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                <button
                  type="button"
                  onClick={() => setTextQuery("What are the primary causes of climate change?")}
                  className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs text-zinc-400 hover:border-white/20 hover:text-zinc-200 transition-colors cursor-pointer"
                >
                  "What are the primary causes of climate change?"
                </button>
                <button
                  type="button"
                  onClick={() => setTextQuery("जलवायु परिवर्तन के मुख्य कारण क्या हैं?")}
                  className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs text-zinc-400 hover:border-white/20 hover:text-zinc-200 transition-colors cursor-pointer"
                >
                  "जलवायु परिवर्तन के मुख्य कारण क्या हैं?"
                </button>
              </div>
            </div>
          )}
        </main>

        <footer className="mt-16 border-t border-white/[0.06] pt-6 flex flex-wrap items-center justify-between gap-4 font-mono text-xs text-zinc-600">
          <div>
            API: <span className="text-zinc-400">{API_BASE_URL}</span>
          </div>
          <div>VAANI (वाणी) · Multilingual Voice RAG</div>
        </footer>
      </div>
    </div>
  );
}
