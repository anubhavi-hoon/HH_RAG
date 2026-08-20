"""
Structured I/O Schemas for Multilingual RAG Orchestration.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Defines clean, typed data contracts between retrieval, LLM generation,
and future API/voice presentation layers.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ResponseStatus(str, Enum):
    """Controlled response status values for FinalResponse."""
    SUCCESS = "success"
    REFUSED = "refused"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    ERROR = "error"


@dataclass
class QueryRequest:
    """
    Represents the normalized user request entering the RAG harness.
    """
    query: str
    language: Optional[str] = None
    request_id: Optional[str] = None
    require_grounding: bool = False

    def __post_init__(self):
        if not isinstance(self.query, str):
            raise TypeError("query must be a string.")
        cleaned = self.query.strip()
        if not cleaned:
            raise ValueError("query cannot be empty or whitespace-only.")
        self.query = cleaned

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryRequest":
        return cls(
            query=data["query"],
            language=data.get("language"),
            request_id=data.get("request_id"),
            require_grounding=data.get("require_grounding", False),
        )


@dataclass
class RetrievedChunk:
    """
    Represents a single retrieved passage/chunk from the vector index.
    """
    chunk_id: str
    text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievedChunk":
        return cls(
            chunk_id=data["chunk_id"],
            text=data["text"],
            score=float(data["score"]),
            metadata=data.get("metadata"),
        )


@dataclass
class RetrievalResult:
    """
    Represents the complete retrieval result passed into orchestration.
    """
    query: str
    chunks: List[RetrievedChunk]
    retrieval_count: int
    retrieval_latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "retrieval_count": self.retrieval_count,
            "retrieval_latency_ms": self.retrieval_latency_ms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievalResult":
        chunks = [
            RetrievedChunk.from_dict(c) if isinstance(c, dict) else c
            for c in data.get("chunks", [])
        ]
        return cls(
            query=data["query"],
            chunks=chunks,
            retrieval_count=data.get("retrieval_count", len(chunks)),
            retrieval_latency_ms=data.get("retrieval_latency_ms"),
        )


@dataclass
class LLMRequest:
    """
    Represents the structured request sent to the LLM generation layer.
    """
    query: str
    language: Optional[str] = None
    context: List[RetrievedChunk] = field(default_factory=list)
    system_instructions: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "language": self.language,
            "context": [chunk.to_dict() for chunk in self.context],
            "system_instructions": self.system_instructions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMRequest":
        context = [
            RetrievedChunk.from_dict(c) if isinstance(c, dict) else c
            for c in data.get("context", [])
        ]
        return cls(
            query=data["query"],
            language=data.get("language"),
            context=context,
            system_instructions=data.get("system_instructions"),
        )


@dataclass
class LLMResponse:
    """
    Represents the raw structured result returned by the LLM layer.
    """
    answer: str
    language: Optional[str] = None
    model: Optional[str] = None
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMResponse":
        return cls(
            answer=data["answer"],
            language=data.get("language"),
            model=data.get("model"),
            latency_ms=data.get("latency_ms"),
        )


@dataclass
class FinalResponse:
    """
    Final stable contract consumed by API, presentation, and voice layers.
    """
    answer: str
    status: ResponseStatus = ResponseStatus.SUCCESS
    reason: Optional[str] = None
    language: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if isinstance(self.status, str):
            try:
                self.status = ResponseStatus(self.status)
            except ValueError:
                valid_values = [s.value for s in ResponseStatus]
                raise ValueError(
                    f"Invalid status '{self.status}'. Must be one of: {valid_values}"
                )

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["status"] = self.status.value
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinalResponse":
        status_val = data.get("status", ResponseStatus.SUCCESS)
        if isinstance(status_val, str):
            status_val = ResponseStatus(status_val)
        return cls(
            answer=data["answer"],
            status=status_val,
            reason=data.get("reason"),
            language=data.get("language"),
            request_id=data.get("request_id"),
            metadata=data.get("metadata"),
        )
