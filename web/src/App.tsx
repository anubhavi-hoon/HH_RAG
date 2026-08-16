import { useCallback, useEffect, useRef, useState } from "react";

import { API_BASE_URL, RagApiError, checkHealth, queryRag, voiceRag } from "./api/rag";
import { useVoiceRecorder } from "./hooks/useVoiceRecorder";
import { AnswerPanel } from "./components/AnswerPanel";
import { LatencyMetricsPanel } from "./components/LatencyMetrics";
import { SourcesPanel } from "./components/SourcesPanel";
import { StatusIndicator } from "./components/StatusIndicator";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { VoiceButton } from "./components/VoiceButton";
import type { BackendStatus, InteractionState, RagResult } from "./types/rag";

const HEALTH_POLL_MS = 20_000;

function toFriendlyMessage(error: unknown): string {
  if (error instanceof RagApiError) return error.message;
  return "Something went wrong while contacting the backend. Please try again.";
}

export default function App() {
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

  const busy = interaction === "processing";

  return (
    <div className="min-h-screen">
      <div className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8 sm:py-14">
        <header className="flex flex-wrap items-start justify-between gap-4 pb-10">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
              HH RAG
            </h1>
            <p className="mt-1 text-sm text-zinc-500">
              Multilingual Voice-Enabled RAG
            </p>
          </div>
          <StatusIndicator status={backendStatus} service={serviceName} />
        </header>

        <main className="space-y-8">
          <div className="flex flex-col items-center gap-8 border-t border-zinc-900 py-12">
            <VoiceButton
              state={interaction}
              disabled={!recorder.isSupported}
              onToggle={() => void handleToggleRecording()}
            />

            {!recorder.isSupported ? (
              <p className="text-xs text-amber-300">
                This browser does not support microphone recording. Use the text
                input below.
              </p>
            ) : null}

            <form
              onSubmit={handleTextSubmit}
              className="flex w-full max-w-xl flex-col gap-3 sm:flex-row"
            >
              <label htmlFor="text-query" className="sr-only">
                Ask a question
              </label>
              <input
                id="text-query"
                type="text"
                value={textQuery}
                onChange={(event) => setTextQuery(event.target.value)}
                placeholder="Ask a question..."
                autoComplete="off"
                disabled={busy}
                className="flex-1 rounded-md border border-zinc-800 bg-zinc-950 px-4 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus-visible:border-zinc-600 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-500 disabled:opacity-60"
              />
              <button
                type="submit"
                disabled={busy}
                className="rounded-md border border-zinc-700 bg-zinc-900 px-5 py-2.5 text-sm font-medium text-zinc-100 transition-colors hover:border-zinc-500 hover:bg-zinc-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-200 focus-visible:ring-offset-2 focus-visible:ring-offset-black disabled:cursor-not-allowed disabled:opacity-60"
              >
                {busy ? "Sending..." : "Send"}
              </button>
            </form>
          </div>

          {errorMessage ? (
            <div
              role="alert"
              className="rounded-md border border-rose-900 bg-rose-950/30 px-4 py-3 text-sm text-rose-200"
            >
              <span aria-hidden="true" className="mr-2 font-mono">
                ✕
              </span>
              {errorMessage}
            </div>
          ) : null}

          {result ? (
            <>
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
              />
              <SourcesPanel sources={result.response.sources} />
              <LatencyMetricsPanel
                latency={result.response.latency}
                clientTotalMs={result.clientTotalMs}
              />
            </>
          ) : (
            <p className="border-t border-zinc-900 pt-8 text-sm text-zinc-600">
              Ask a question by voice or text to see the transcript, grounded
              answer, retrieved sources and stage-by-stage latency.
            </p>
          )}
        </main>

        <footer className="mt-16 border-t border-zinc-900 pt-6 font-mono text-[11px] text-zinc-700">
          API {API_BASE_URL} · mock retrieval pipeline
        </footer>
      </div>
    </div>
  );
}
