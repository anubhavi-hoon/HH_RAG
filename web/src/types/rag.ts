/** Types mirroring the FastAPI contract in src/api/schemas/rag.py. */

export type Language = "hi" | "en";

export interface Source {
  chunk_id: string;
  text: string;
  score: number;
  language: Language;
  /** Chunking strategy; null until the retrieval pipeline reports it. */
  strategy: string | null;
  doc_id: string | null;
}

export interface LatencyMetrics {
  stt_ms: number;
  embedding_ms: number;
  retrieval_ms: number;
  generation_ms: number;
  guardrail_ms: number;
  /** Server-side wall clock for the RAG service call. Not a sum of the stages. */
  total_ms: number;
}

export interface RagResponse {
  transcript: string | null;
  query: string;
  language: Language;
  answer: string;
  grounded: boolean;
  confidence: number;
  sources: Source[];
  latency: LatencyMetrics;
}

/** A completed call: the server payload plus latency only the client can observe. */
export interface RagResult {
  response: RagResponse;
  /** Round trip measured here: just before fetch() until the body is parsed. */
  clientTotalMs: number;
  /** Full server request duration from the X-Process-Time-Ms header, if present. */
  serverProcessMs: number | null;
  requestId: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

/** Finite state of the voice/query interaction. */
export type InteractionState =
  | "idle"
  | "recording"
  | "processing"
  | "complete"
  | "error";

export type BackendStatus = "checking" | "online" | "offline";
