"""The seam between the API layer and the RAG pipeline.

    CURRENT:  API -> MockRAGService
    FUTURE:   API -> RealRAGService -> Retriever + Generator + Guardrails

Routes depend only on :class:`RAGService`, the domain errors below, and the
schemas in ``src.api.schemas.rag``. Swapping the implementation therefore never
changes the HTTP contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Optional

from src.api.schemas.rag import RagResponse


class ErrorCode(str, Enum):
    """Stable machine-readable error codes returned to clients."""

    INVALID_QUERY = "INVALID_QUERY"
    AUDIO_INVALID = "AUDIO_INVALID"
    STT_FAILED = "STT_FAILED"
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    GENERATION_FAILED = "GENERATION_FAILED"
    GUARDRAIL_FAILED = "GUARDRAIL_FAILED"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class RagServiceError(Exception):
    """Base class for failures a RAG implementation can report to the API layer.

    ``message`` is rendered verbatim to the client, so it must never contain
    internal detail such as stack traces or credentials.
    """

    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    status_code: int = 500

    def __init__(self, message: str, *, cause: Optional[BaseException] = None) -> None:
        super().__init__(message)
        self.message = message
        self.__cause__ = cause


class InvalidQueryError(RagServiceError):
    code = ErrorCode.INVALID_QUERY
    status_code = 422


class AudioInvalidError(RagServiceError):
    code = ErrorCode.AUDIO_INVALID
    status_code = 422


class SttFailedError(RagServiceError):
    code = ErrorCode.STT_FAILED
    status_code = 502


class RetrievalFailedError(RagServiceError):
    code = ErrorCode.RETRIEVAL_FAILED
    status_code = 503


class GenerationFailedError(RagServiceError):
    code = ErrorCode.GENERATION_FAILED
    status_code = 502


class GuardrailFailedError(RagServiceError):
    code = ErrorCode.GUARDRAIL_FAILED
    status_code = 500


@dataclass(frozen=True)
class AudioInput:
    """Uploaded audio, decoupled from the web framework's file object."""

    filename: str
    content_type: str
    data: bytes


class RAGService(ABC):
    """Contract every RAG implementation (mock or real) must satisfy."""

    @abstractmethod
    def query(self, query: str, require_grounding: bool = False) -> RagResponse:
        """Answer a text question.

        Raises:
            InvalidQueryError, RetrievalFailedError, GenerationFailedError,
            GuardrailFailedError.
        """

    @abstractmethod
    def voice(self, audio: AudioInput) -> RagResponse:
        """Transcribe audio and answer the resulting question.

        Raises:
            AudioInvalidError, SttFailedError, and the errors of :meth:`query`.
        """


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    """Provide the active implementation. Routes inject this via ``Depends``."""
    import os

    use_real = os.getenv("HH_RAG_USE_REAL", "false").lower() in ("1", "true", "yes")
    use_mock = os.getenv("HH_RAG_USE_MOCK", "true" if not use_real else "false").lower() in ("1", "true", "yes")

    if not use_mock or use_real:
        from src.services.real_rag import RealRAGService
        return RealRAGService()

    from src.services.mock_rag import MockRAGService
    return MockRAGService()

