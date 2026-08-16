"""Pydantic models defining the stable request/response contract for the RAG API.

These schemas are intentionally implementation-agnostic: the mock service can be
swapped for the real retrieval + generation pipeline without changing them.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from src.config import Language


class Source(BaseModel):
    """A single retrieved chunk used to ground the answer."""

    chunk_id: str
    text: str
    score: float = Field(ge=0.0, le=1.0)
    language: Language
    #: Chunking strategy that produced the chunk; null until retrieval reports it.
    strategy: Optional[str] = None
    doc_id: Optional[str] = None


class LatencyMetrics(BaseModel):
    """Server-side latency, in milliseconds. Every value is measured, never estimated.

    There are three distinct latencies in this system; only the first two live here:

    * **stage fields** (``stt_ms`` ... ``guardrail_ms``) - measured duration of that
      individual operation. ``0`` means the stage did not run or was not measured,
      never "instant".
    * ``total_ms`` - wall-clock duration of the whole RAG service call, measured by
      the API route with :class:`src.utils.timing.Timer`. It is **not** the sum of
      the stage fields; the difference is un-instrumented work between stages.
    * ``client_total_ms`` - HTTP round trip measured by the caller (frontend or
      benchmark). It is deliberately **not** part of this schema, because the
      server cannot observe it.

    Therefore: ``sum(stages) <= total_ms <= client_total_ms``.
    """

    stt_ms: float = 0
    embedding_ms: float = 0
    retrieval_ms: float = 0
    generation_ms: float = 0
    guardrail_ms: float = 0
    total_ms: float = 0


class RagResponse(BaseModel):
    """Unified response returned by both the text and voice endpoints."""

    transcript: Optional[str] = None
    query: str
    language: Language
    answer: str
    grounded: bool
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[Source] = Field(default_factory=list)
    latency: LatencyMetrics = Field(default_factory=LatencyMetrics)


class QueryRequest(BaseModel):
    """Text query submitted to /api/query."""

    query: str = Field(min_length=1, max_length=2000)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be empty or whitespace only")
        return stripped


class HealthResponse(BaseModel):
    """Liveness payload for /api/health."""

    status: str
    service: str
    version: str
