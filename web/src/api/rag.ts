/**
 * Single point of contact with the HH RAG backend.
 *
 * UI components must never call fetch() directly — everything goes through this
 * module so the mock backend can be swapped for the real RAG pipeline without
 * touching any component.
 */

import type {
  HealthResponse,
  LatencyMetrics,
  RagResponse,
  RagResult,
  Source,
} from "../types/rag";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

const REQUEST_TIMEOUT_MS = 30_000;
const HEALTH_TIMEOUT_MS = 5_000;
const REQUEST_ID_HEADER = "X-Request-ID";
const PROCESS_TIME_HEADER = "X-Process-Time-Ms";

/** Error carrying a message that is safe to render directly in the UI. */
export class RagApiError extends Error {
  readonly status?: number;
  readonly code?: string;
  readonly requestId?: string;

  constructor(
    message: string,
    options: { status?: number; code?: string; requestId?: string } = {},
  ) {
    super(message);
    this.name = "RagApiError";
    this.status = options.status;
    this.code = options.code;
    this.requestId = options.requestId;
  }
}

const MIME_EXTENSIONS: Record<string, string> = {
  "audio/webm": "webm",
  "audio/ogg": "ogg",
  "audio/mp4": "mp4",
  "audio/mpeg": "mp3",
  "audio/wav": "wav",
  "audio/aac": "aac",
};

function audioFileName(blob: Blob): string {
  const baseType = (blob.type || "audio/webm").split(";")[0].trim();
  return `recording.${MIME_EXTENSIONS[baseType] ?? "webm"}`;
}

/** Raw transport result: decoded body plus latency only the caller can observe. */
interface TransportResult {
  body: unknown;
  clientTotalMs: number;
  serverProcessMs: number | null;
  requestId: string | null;
}

async function requestJson(
  path: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<TransportResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  // Round trip is measured here and nowhere else: the clock starts immediately
  // before the request leaves and stops once the body has been fully read.
  const startedAt = performance.now();

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new RagApiError(
        "The request timed out. The backend took too long to respond.",
      );
    }
    throw new RagApiError(
      `Cannot reach the HH RAG backend at ${API_BASE_URL}. Make sure it is running.`,
    );
  } finally {
    clearTimeout(timer);
  }

  const requestId = response.headers.get(REQUEST_ID_HEADER);
  const processHeader = Number(response.headers.get(PROCESS_TIME_HEADER));
  const serverProcessMs = Number.isFinite(processHeader) ? processHeader : null;

  if (!response.ok) {
    const { code, message } = await parseErrorBody(response);
    throw new RagApiError(message, {
      status: response.status,
      code,
      requestId: requestId ?? undefined,
    });
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new RagApiError("The backend returned a response that could not be read.", {
      status: response.status,
      requestId: requestId ?? undefined,
    });
  }

  return {
    body,
    clientTotalMs: performance.now() - startedAt,
    serverProcessMs,
    requestId,
  };
}

/**
 * Backend errors use `{ error: { code, message } }`. FastAPI's own `detail`
 * shape is still handled so an older backend build stays readable.
 */
async function parseErrorBody(
  response: Response,
): Promise<{ code?: string; message: string }> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    body = undefined;
  }

  const envelope = (body as { error?: { code?: unknown; message?: unknown } })?.error;
  if (envelope && typeof envelope.message === "string" && envelope.message.trim()) {
    return {
      code: typeof envelope.code === "string" ? envelope.code : undefined,
      message: envelope.message,
    };
  }

  const detail = (body as { detail?: unknown })?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return { message: detail };
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) =>
        item && typeof item === "object" && typeof (item as { msg?: unknown }).msg === "string"
          ? ((item as { msg: string }).msg)
          : null,
      )
      .filter((msg): msg is string => Boolean(msg));
    if (messages.length) {
      return { message: messages.join(" · ").replace(/^Value error,\s*/i, "") };
    }
  }

  return { message: fallbackMessage(response.status) };
}

function fallbackMessage(status: number): string {
  if (status >= 500) {
    return "The backend hit an internal error. Check the API logs and try again.";
  }
  if (status === 413) return "That recording is too large to upload.";
  if (status === 415) return "That audio format is not supported.";
  if (status === 422) return "The request was rejected as invalid.";
  if (status === 404) return "Endpoint not found on the backend.";
  return `Request failed with status ${status}.`;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function parseLatency(value: unknown): LatencyMetrics {
  const raw = (value ?? {}) as Record<string, unknown>;
  const read = (key: keyof LatencyMetrics) =>
    isFiniteNumber(raw[key]) ? (raw[key] as number) : 0;
  return {
    stt_ms: read("stt_ms"),
    embedding_ms: read("embedding_ms"),
    retrieval_ms: read("retrieval_ms"),
    generation_ms: read("generation_ms"),
    guardrail_ms: read("guardrail_ms"),
    total_ms: read("total_ms"),
  };
}

function parseSources(value: unknown): Source[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item, index) => {
    if (!item || typeof item !== "object") return [];
    const raw = item as Record<string, unknown>;
    return [
      {
        chunk_id: typeof raw.chunk_id === "string" ? raw.chunk_id : `chunk-${index}`,
        text: typeof raw.text === "string" ? raw.text : "",
        score: isFiniteNumber(raw.score) ? raw.score : 0,
        language: raw.language === "hi" ? "hi" : "en",
        strategy: typeof raw.strategy === "string" ? raw.strategy : null,
        doc_id: typeof raw.doc_id === "string" ? raw.doc_id : null,
      },
    ];
  });
}

/** Narrow an unknown payload to RagResponse, tolerating optional fields. */
function parseRagResponse(payload: unknown): RagResponse {
  if (!payload || typeof payload !== "object") {
    throw new RagApiError("The backend returned an unexpected response.");
  }
  const raw = payload as Record<string, unknown>;

  if (typeof raw.answer !== "string" || typeof raw.query !== "string") {
    throw new RagApiError("The backend returned an incomplete response.");
  }

  return {
    transcript: typeof raw.transcript === "string" ? raw.transcript : null,
    query: raw.query,
    language: raw.language === "hi" ? "hi" : "en",
    answer: raw.answer,
    grounded: raw.grounded === true,
    confidence: isFiniteNumber(raw.confidence) ? raw.confidence : 0,
    sources: parseSources(raw.sources),
    latency: parseLatency(raw.latency),
  };
}

/** POST /api/query — text question. */
export async function queryRag(query: string): Promise<RagResult> {
  const trimmed = query.trim();
  if (!trimmed) {
    throw new RagApiError("Enter a question before sending.");
  }

  const transport = await requestJson(
    "/api/query",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: trimmed }),
    },
    REQUEST_TIMEOUT_MS,
  );

  return toRagResult(transport);
}

/** POST /api/voice — multipart audio upload. */
export async function voiceRag(audioBlob: Blob): Promise<RagResult> {
  if (!audioBlob || audioBlob.size === 0) {
    throw new RagApiError("No audio was captured. Try recording again.");
  }

  const form = new FormData();
  // Content-Type is intentionally left to the browser so the multipart boundary is set.
  form.append("file", audioBlob, audioFileName(audioBlob));

  const transport = await requestJson(
    "/api/voice",
    { method: "POST", body: form },
    REQUEST_TIMEOUT_MS,
  );

  return toRagResult(transport);
}

function toRagResult(transport: TransportResult): RagResult {
  return {
    response: parseRagResponse(transport.body),
    clientTotalMs: transport.clientTotalMs,
    serverProcessMs: transport.serverProcessMs,
    requestId: transport.requestId,
  };
}

/** GET /api/health — used by the status indicator. */
export async function checkHealth(): Promise<HealthResponse> {
  const { body } = await requestJson("/api/health", { method: "GET" }, HEALTH_TIMEOUT_MS);
  const raw = (body ?? {}) as Record<string, unknown>;
  if (typeof raw.status !== "string" || typeof raw.service !== "string") {
    throw new RagApiError("Health endpoint returned an unexpected response.");
  }
  return {
    status: raw.status,
    service: raw.service,
    version: typeof raw.version === "string" ? raw.version : "unknown",
  };
}

export { API_BASE_URL };
