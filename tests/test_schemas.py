"""Unit tests for structured orchestration schemas."""

import json
import pytest

from src.orchestration.schemas import (
    FinalResponse,
    LLMRequest,
    LLMResponse,
    QueryRequest,
    RetrievalResult,
    RetrievedChunk,
    ResponseStatus,
)


def test_query_request_valid():
    """Test creating a valid QueryRequest with and without optional fields."""
    req = QueryRequest(query="  What is artificial intelligence?  ", language="en", request_id="req_123")
    assert req.query == "What is artificial intelligence?"
    assert req.language == "en"
    assert req.request_id == "req_123"

    req_simple = QueryRequest(query="नमस्ते")
    assert req_simple.query == "नमस्ते"
    assert req_simple.language is None
    assert req_simple.request_id is None


def test_query_request_empty_and_whitespace_rejected():
    """Test that empty, whitespace-only, or non-string queries are rejected."""
    with pytest.raises(ValueError, match="query cannot be empty"):
        QueryRequest(query="")

    with pytest.raises(ValueError, match="query cannot be empty"):
        QueryRequest(query="   \t\n  ")

    with pytest.raises(TypeError, match="query must be a string"):
        QueryRequest(query=None)  # type: ignore


def test_retrieved_chunk():
    """Test RetrievedChunk data model."""
    chunk = RetrievedChunk(
        chunk_id="chunk_msmarco_1",
        text="Sample text content for retrieval.",
        score=0.8765,
        metadata={"source": "msmarco", "parent_id": "doc_10"},
    )
    assert chunk.chunk_id == "chunk_msmarco_1"
    assert chunk.text == "Sample text content for retrieval."
    assert chunk.score == 0.8765
    assert chunk.metadata == {"source": "msmarco", "parent_id": "doc_10"}


def test_retrieval_result():
    """Test RetrievalResult holding multiple chunks and latency."""
    chunks = [
        RetrievedChunk(chunk_id="c1", text="text 1", score=0.9),
        RetrievedChunk(chunk_id="c2", text="text 2", score=0.8),
    ]
    res = RetrievalResult(
        query="test query",
        chunks=chunks,
        retrieval_count=len(chunks),
        retrieval_latency_ms=18.5,
    )
    assert res.query == "test query"
    assert len(res.chunks) == 2
    assert res.retrieval_count == 2
    assert res.retrieval_latency_ms == 18.5


def test_llm_request():
    """Test LLMRequest structuring query, context, and instructions."""
    chunks = [RetrievedChunk(chunk_id="c1", text="context snippet", score=0.85)]
    req = LLMRequest(
        query="Explain X",
        language="en",
        context=chunks,
        system_instructions="Answer concisely.",
    )
    assert req.query == "Explain X"
    assert req.language == "en"
    assert len(req.context) == 1
    assert req.system_instructions == "Answer concisely."


def test_llm_response():
    """Test LLMResponse structure."""
    resp = LLMResponse(
        answer="X is an important concept.",
        language="en",
        model="llama-3.1-8b-instant",
        latency_ms=145.2,
    )
    assert resp.answer == "X is an important concept."
    assert resp.model == "llama-3.1-8b-instant"
    assert resp.latency_ms == 145.2


def test_final_response_statuses():
    """Test FinalResponse across all controlled statuses."""
    # 1. Success
    r_success = FinalResponse(
        answer="Grounded answer.",
        status=ResponseStatus.SUCCESS,
        language="en",
        request_id="req_1",
    )
    assert r_success.status == ResponseStatus.SUCCESS
    assert r_success.answer == "Grounded answer."

    # 2. Insufficient Context
    r_insufficient = FinalResponse(
        answer="Available context is insufficient.",
        status=ResponseStatus.INSUFFICIENT_CONTEXT,
        reason="No matching documents found with sufficient similarity",
    )
    assert r_insufficient.status == ResponseStatus.INSUFFICIENT_CONTEXT
    assert r_insufficient.reason == "No matching documents found with sufficient similarity"

    # 3. Refused
    r_refused = FinalResponse(
        answer="Request refused due to policy constraints.",
        status=ResponseStatus.REFUSED,
        reason="Safety violation",
    )
    assert r_refused.status == ResponseStatus.REFUSED

    # 4. Error
    r_error = FinalResponse(
        answer="An error occurred processing the request.",
        status=ResponseStatus.ERROR,
        reason="Upstream timeout",
    )
    assert r_error.status == ResponseStatus.ERROR

    # 5. String status auto-conversion
    r_str = FinalResponse(answer="Ok", status="success")  # type: ignore
    assert r_str.status == ResponseStatus.SUCCESS

    # 6. Invalid status rejected
    with pytest.raises(ValueError, match="Invalid status"):
        FinalResponse(answer="Fail", status="invalid_status")  # type: ignore


def test_json_serialization_and_roundtrip():
    """Test JSON compatibility and roundtripping for all schemas."""
    # QueryRequest
    q = QueryRequest(query="Hello", language="en", request_id="q1")
    q_dict = q.to_dict()
    assert json.loads(json.dumps(q_dict)) == q_dict
    assert QueryRequest.from_dict(q_dict) == q

    # RetrievedChunk
    chunk = RetrievedChunk(chunk_id="c1", text="text", score=0.95, metadata={"k": "v"})
    c_dict = chunk.to_dict()
    assert json.loads(json.dumps(c_dict)) == c_dict
    assert RetrievedChunk.from_dict(c_dict) == chunk

    # RetrievalResult
    ret = RetrievalResult(query="Hello", chunks=[chunk], retrieval_count=1, retrieval_latency_ms=12.3)
    ret_dict = ret.to_dict()
    assert json.loads(json.dumps(ret_dict)) == ret_dict
    assert RetrievalResult.from_dict(ret_dict) == ret

    # LLMRequest
    llm_req = LLMRequest(query="Hello", context=[chunk], system_instructions="Be brief")
    llm_req_dict = llm_req.to_dict()
    assert json.loads(json.dumps(llm_req_dict)) == llm_req_dict
    assert LLMRequest.from_dict(llm_req_dict) == llm_req

    # LLMResponse
    llm_resp = LLMResponse(answer="Hi", model="llama-3.1-8b-instant", latency_ms=100.0)
    llm_resp_dict = llm_resp.to_dict()
    assert json.loads(json.dumps(llm_resp_dict)) == llm_resp_dict
    assert LLMResponse.from_dict(llm_resp_dict) == llm_resp

    # FinalResponse
    fin = FinalResponse(
        answer="Hi",
        status=ResponseStatus.SUCCESS,
        reason=None,
        language="en",
        request_id="r1",
        metadata={"latency": 150},
    )
    fin_dict = fin.to_dict()
    assert json.loads(json.dumps(fin_dict)) == fin_dict
    assert FinalResponse.from_dict(fin_dict) == fin
