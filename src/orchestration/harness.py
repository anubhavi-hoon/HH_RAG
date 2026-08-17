"""
RAG Orchestration Harness.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Orchestrates the end-to-end execution flow:
QueryRequest -> Retrieval -> LLMRequest -> LLMResponse -> FinalResponse.
"""

import logging
import sys
import time
from typing import Any, Callable, Dict, List, Optional

from src.orchestration.grounding import GroundingResult, verify_grounding
from src.orchestration.guardrails import (
    DEFAULT_SIMILARITY_THRESHOLD,
    context_sufficiency_guardrail,
    safety_guardrail,
    validate_input_guardrail,
)
from src.orchestration.schemas import (
    FinalResponse,
    LLMRequest,
    LLMResponse,
    QueryRequest,
    ResponseStatus,
    RetrievalResult,
    RetrievedChunk,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("rag_harness")


class RAGHarness:
    """
    Lightweight, strongly-typed orchestrator connecting retrieval, guardrails, Groq LLM, and grounding.
    """

    def __init__(
        self,
        retriever_fn: Optional[Callable[[str, int], List[Dict[str, Any]]]] = None,
        generator_fn: Optional[Callable[..., Dict[str, Any]]] = None,
        grounding_fn: Optional[Callable[..., GroundingResult]] = None,
        top_k: int = 3,
        default_model: Optional[str] = None,
        max_tokens: int = 1024,
        min_similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ):
        """
        Initializes the harness with dependency injection for clean testing and modularity.
        """
        if retriever_fn is None:
            from src.retrieval.retriever import retrieve_chunks
            self.retriever_fn = retrieve_chunks
        else:
            self.retriever_fn = retriever_fn

        if generator_fn is None:
            from src.llm.groq_client import generate_answer
            self.generator_fn = generate_answer
        else:
            self.generator_fn = generator_fn

        if grounding_fn is None:
            self.grounding_fn = verify_grounding
        else:
            self.grounding_fn = grounding_fn

        self.top_k = top_k
        self.default_model = default_model
        self.max_tokens = max_tokens
        self.min_similarity_threshold = min_similarity_threshold


    def run(self, request: QueryRequest) -> FinalResponse:
        """
        Executes the full RAG orchestration pipeline with guardrails:
        QueryRequest -> Input/Safety Guardrails -> Retrieval -> Context Guardrail -> Groq -> FinalResponse.

        Args:
            request: Validated QueryRequest object.

        Returns:
            FinalResponse object with status, answer, and metadata.
        """
        t_start = time.perf_counter()

        # 1. Validate Input Request Format
        if not isinstance(request, QueryRequest):
            try:
                if isinstance(request, str):
                    request = QueryRequest(query=request)
                elif isinstance(request, dict):
                    request = QueryRequest.from_dict(request)
                else:
                    return FinalResponse(
                        answer="Invalid request format.",
                        status=ResponseStatus.ERROR,
                        reason="invalid_request_type",
                        request_id=getattr(request, "request_id", None),
                    )
            except Exception as e:
                logger.error(f"Failed to parse QueryRequest: {e}")
                return FinalResponse(
                    answer="Invalid query request.",
                    status=ResponseStatus.ERROR,
                    reason="request_validation_failed",
                )

        req_id = request.request_id
        req_lang = request.language

        # 2. Input Validation Guardrail
        is_valid, err_reason, err_msg = validate_input_guardrail(request.query)
        if not is_valid:
            return FinalResponse(
                answer=err_msg or "Invalid query.",
                status=ResponseStatus.ERROR,
                reason=err_reason,
                language=req_lang,
                request_id=req_id,
            )

        # 3. Deterministic Safety Guardrail (No LLM / No Network calls)
        is_safe, refusal_reason, refusal_msg = safety_guardrail(request.query)
        if not is_safe:
            return FinalResponse(
                answer=refusal_msg or "Request refused.",
                status=ResponseStatus.REFUSED,
                reason=refusal_reason,
                language=req_lang,
                request_id=req_id,
            )

        # 4. Retrieval Stage
        t_ret_start = time.perf_counter()
        try:
            raw_chunks = self.retriever_fn(request.query, self.top_k)
        except Exception as e:
            logger.error(f"Retrieval error for query '{request.query}': {e}", exc_info=True)
            return FinalResponse(
                answer="An error occurred while retrieving relevant context.",
                status=ResponseStatus.ERROR,
                reason="retrieval_failure",
                language=req_lang,
                request_id=req_id,
            )
        t_ret_end = time.perf_counter()
        ret_latency_ms = (t_ret_end - t_ret_start) * 1000.0

        # 5. Convert to RetrievalResult & RetrievedChunk models
        retrieved_chunks: List[RetrievedChunk] = []
        for c in raw_chunks:
            chunk_metadata = {k: v for k, v in c.items() if k not in ("chunk_id", "text", "score")}
            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=str(c.get("chunk_id", "")),
                    text=str(c.get("text", "")),
                    score=float(c.get("score", 0.0)),
                    metadata=chunk_metadata,
                )
            )

        retrieval_result = RetrievalResult(
            query=request.query,
            chunks=retrieved_chunks,
            retrieval_count=len(retrieved_chunks),
            retrieval_latency_ms=round(ret_latency_ms, 2),
        )

        # 6. Context Sufficiency Guardrail (Evaluates relevance score & availability)
        is_sufficient, ctx_reason, ctx_msg = context_sufficiency_guardrail(
            retrieved_chunks, min_similarity_threshold=self.min_similarity_threshold
        )
        if not is_sufficient:
            t_total_end = time.perf_counter()
            total_latency_ms = (t_total_end - t_start) * 1000.0
            return FinalResponse(
                answer=ctx_msg or "Available context is insufficient.",
                status=ResponseStatus.INSUFFICIENT_CONTEXT,
                reason=ctx_reason,
                language=req_lang,
                request_id=req_id,
                metadata={
                    "retrieval_count": retrieval_result.retrieval_count,
                    "retrieval_latency_ms": retrieval_result.retrieval_latency_ms,
                    "total_latency_ms": round(total_latency_ms, 2),
                },
            )

        # 7. Construct LLMRequest
        llm_request = LLMRequest(
            query=request.query,
            language=req_lang,
            context=retrieved_chunks,
        )


        # 5. LLM Generation Stage
        # Pass raw chunk dictionaries to existing generate_answer implementation
        llm_chunks_payload = [
            {
                "chunk_id": c.chunk_id,
                "text": c.text,
                "score": c.score,
                "language": (c.metadata or {}).get("language", req_lang or ""),
                **(c.metadata or {}),
            }
            for c in llm_request.context
        ]

        try:
            gen_kwargs: Dict[str, Any] = {
                "question": llm_request.query,
                "retrieved_chunks": llm_chunks_payload,
                "max_tokens": self.max_tokens,
            }
            if self.default_model:
                gen_kwargs["model_name"] = self.default_model

            raw_llm_result = self.generator_fn(**gen_kwargs)
        except Exception as e:
            logger.error(f"LLM generation error for query '{request.query}': {e}", exc_info=True)
            return FinalResponse(
                answer="An error occurred while generating the answer.",
                status=ResponseStatus.ERROR,
                reason="llm_generation_failure",
                language=req_lang,
                request_id=req_id,
            )

        # 6. Validate & Convert to LLMResponse
        if not isinstance(raw_llm_result, dict):
            logger.error(f"Malformed LLM result (not a dict): {raw_llm_result}")
            return FinalResponse(
                answer="Invalid response structure returned by generation layer.",
                status=ResponseStatus.ERROR,
                reason="malformed_llm_response",
                language=req_lang,
                request_id=req_id,
            )

        raw_answer = raw_llm_result.get("answer")
        if not raw_answer or not isinstance(raw_answer, str) or not raw_answer.strip():
            logger.error(f"Empty answer text received from LLM: {raw_llm_result}")
            return FinalResponse(
                answer="Empty answer generated by LLM.",
                status=ResponseStatus.ERROR,
                reason="empty_llm_answer",
                language=req_lang,
                request_id=req_id,
            )

        clean_answer = raw_answer.strip()
        llm_response = LLMResponse(
            answer=clean_answer,
            language=req_lang,
            model=raw_llm_result.get("model"),
            latency_ms=raw_llm_result.get("llm_latency_ms"),
        )

        # 7. Output Grounding Guardrail (Strategy A: Lexical & Numerical Verification)
        grounding_res = self.grounding_fn(
            query=request.query,
            retrieved_chunks=retrieved_chunks,
            answer=llm_response.answer,
            language=req_lang,
        )

        t_total_end = time.perf_counter()
        total_latency_ms = (t_total_end - t_start) * 1000.0

        if not grounding_res.grounded:
            logger.warning(
                f"Grounding guardrail flagged ungrounded output for query '{request.query}': {grounding_res.reason} ({grounding_res.unsupported_claims})"
            )
            return FinalResponse(
                answer="The available context does not contain sufficient support to verify this answer.",
                status=ResponseStatus.INSUFFICIENT_CONTEXT,
                reason="answer_not_grounded",
                language=req_lang,
                request_id=req_id,
                metadata={
                    "retrieval_count": retrieval_result.retrieval_count,
                    "retrieval_latency_ms": retrieval_result.retrieval_latency_ms,
                    "llm_latency_ms": llm_response.latency_ms,
                    "total_latency_ms": round(total_latency_ms, 2),
                    "model": llm_response.model,
                    "grounding_reason": grounding_res.reason,
                    "grounding_overlap": grounding_res.overlap_score,
                    "unsupported_claims": grounding_res.unsupported_claims,
                },
            )

        # 8. Construct FinalResponse (Success)
        return FinalResponse(
            answer=llm_response.answer,
            status=ResponseStatus.SUCCESS,
            reason=None,
            language=req_lang,
            request_id=req_id,
            metadata={
                "retrieval_count": retrieval_result.retrieval_count,
                "retrieval_latency_ms": retrieval_result.retrieval_latency_ms,
                "llm_latency_ms": llm_response.latency_ms,
                "total_latency_ms": round(total_latency_ms, 2),
                "model": llm_response.model,
                "grounding_reason": grounding_res.reason,
                "grounding_overlap": grounding_res.overlap_score,
                "sources": [c.to_dict() for c in retrieved_chunks],
            },
        )


# Global default harness instance
_DEFAULT_HARNESS: Optional[RAGHarness] = None


def get_harness() -> RAGHarness:
    """Returns a singleton instance of RAGHarness."""
    global _DEFAULT_HARNESS
    if _DEFAULT_HARNESS is None:
        _DEFAULT_HARNESS = RAGHarness()
    return _DEFAULT_HARNESS


def run(request: QueryRequest) -> FinalResponse:
    """
    Public entry point to execute the complete RAG orchestration pipeline.
    """
    return get_harness().run(request)
