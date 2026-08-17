"""
Production RAG Service Adapter.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Connects FastAPI to the Stage 5 RAG Orchestration Harness:
FastAPI -> RAGService -> RealRAGService -> RAGHarness.run() -> FinalResponse -> RagResponse.
"""

import logging
import re
from typing import Optional

from src.api.middleware import current_request_id
from src.api.schemas.rag import LatencyMetrics, RagResponse, Source
from src.config import DEFAULT_LANGUAGE, Language
from src.orchestration.harness import RAGHarness, get_harness
from src.orchestration.schemas import QueryRequest, ResponseStatus
from src.services.rag_service import (
    AudioInput,
    AudioInvalidError,
    InvalidQueryError,
    RAGService,
    SttFailedError,
)
from src.services.sarvam_stt import SarvamSTTService

logger = logging.getLogger("real_rag_service")

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def detect_language(text: str) -> Language:
    """Return Hindi when the text contains Devanagari characters, else English."""
    return Language.HI if _DEVANAGARI_RE.search(text) else DEFAULT_LANGUAGE


class RealRAGService(RAGService):
    """
    Production RAG Service connecting FastAPI to the Stage 5 RAG Harness.
    """

    def __init__(
        self,
        harness: Optional[RAGHarness] = None,
        stt_service: Optional[SarvamSTTService] = None,
    ):
        """
        Initializes the service with dependency injection for clean testing.
        """
        self.harness = harness if harness is not None else get_harness()
        self.stt_service = stt_service if stt_service is not None else SarvamSTTService()

    def query(self, query: str) -> RagResponse:
        """
        Executes a text query through the Stage 5 RAG Harness.
        """
        if not query or not query.strip():
            raise InvalidQueryError("Query must not be empty.")

        clean_query = query.strip()
        lang_enum = detect_language(clean_query)
        lang_str = lang_enum.value

        # Extract correlation request ID from context if available
        req_id = current_request_id()
        if req_id == "-" or not req_id:
            req_id = None

        # 1. Create Stage 5 internal contract
        query_request = QueryRequest(
            query=clean_query,
            language=lang_str,
            request_id=req_id,
        )

        # 2. Execute through RAG Harness (Single entrypoint to RAG pipeline)
        final_response = self.harness.run(query_request)

        # 3. Map FinalResponse to API RagResponse schema
        is_grounded = (final_response.status == ResponseStatus.SUCCESS)

        # Deterministic confidence mapping
        if is_grounded:
            confidence = 0.95
        else:
            confidence = 0.0

        # Sub-stage latency extraction from harness metadata
        meta = final_response.metadata or {}
        latency_metrics = LatencyMetrics(
            stt_ms=0.0,
            embedding_ms=0.0,
            retrieval_ms=float(meta.get("retrieval_latency_ms", 0.0)),
            generation_ms=float(meta.get("llm_latency_ms", 0.0)),
            guardrail_ms=0.0,
            total_ms=0.0,  # Populated by route Timer
        )

        # Extract sources from harness metadata
        api_sources = []
        if is_grounded:
            raw_sources = meta.get("sources", [])
            for s in raw_sources:
                s_meta = s.get("metadata") or {}
                api_sources.append(
                    Source(
                        chunk_id=str(s.get("chunk_id", "")),
                        text=str(s.get("text", "")),
                        score=float(s.get("score", 0.0)),
                        language=s_meta.get("language", DEFAULT_LANGUAGE),
                        strategy=s_meta.get("strategy"),
                        doc_id=s_meta.get("doc_id"),
                    )
                )

        return RagResponse(
            transcript=None,
            query=clean_query,
            language=lang_enum,
            answer=final_response.answer,
            grounded=is_grounded,
            confidence=confidence,
            sources=api_sources,
            latency=latency_metrics,
        )

    def voice(self, audio: AudioInput) -> RagResponse:
        """
        Transcribes audio input via Sarvam STT and answers the transcribed question.
        """
        if audio is None or not audio.data:
            raise AudioInvalidError("Uploaded audio file is empty.")

        stt_result = self.stt_service.transcribe(
            filename=audio.filename,
            content_type=audio.content_type,
            audio_bytes=audio.data,
        )

        transcript = (stt_result.transcript or "").strip()
        if not transcript:
            raise SttFailedError("Speech-to-text produced an empty transcript.")

        response = self.query(transcript)
        response.transcript = transcript
        response.latency.stt_ms = round(stt_result.latency_ms, 3)
        return response

