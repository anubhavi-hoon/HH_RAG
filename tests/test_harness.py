"""Unit tests for RAG orchestration harness including guardrails integration."""

from unittest.mock import MagicMock
import pytest

from src.orchestration.harness import RAGHarness, run
from src.orchestration.schemas import (
    FinalResponse,
    QueryRequest,
    ResponseStatus,
)


@pytest.fixture
def sample_raw_chunks():
    return [
        {
            "rank": 1,
            "chunk_id": "chunk_1",
            "text": "Alan Turing invented the Turing machine in 1936.",
            "language": "en",
            "score": 0.89,
            "parent_passage_id": "doc_1",
        },
        {
            "rank": 2,
            "chunk_id": "chunk_2",
            "text": "The Turing machine is an abstract machine model.",
            "language": "en",
            "score": 0.81,
            "parent_passage_id": "doc_2",
        },
    ]


@pytest.fixture
def mock_retriever(sample_raw_chunks):
    retriever = MagicMock()
    retriever.return_value = sample_raw_chunks
    return retriever


@pytest.fixture
def mock_generator():
    generator = MagicMock()
    generator.return_value = {
        "answer": "Alan Turing invented the Turing machine.",
        "model": "llama-3.1-8b-instant",
        "llm_latency_ms": 142.5,
        "usage": {"prompt_tokens": 120, "completion_tokens": 15},
    }
    return generator


def test_harness_successful_flow(mock_retriever, mock_generator):
    """Test successful end-to-end harness orchestration flow."""
    harness = RAGHarness(
        retriever_fn=mock_retriever,
        generator_fn=mock_generator,
        top_k=2,
    )
    req = QueryRequest(
        query="Who invented the Turing machine?",
        language="en",
        request_id="req_999",
    )

    response = harness.run(req)

    assert isinstance(response, FinalResponse)
    assert response.status == ResponseStatus.SUCCESS
    assert response.answer == "Alan Turing invented the Turing machine."
    assert response.language == "en"
    assert response.request_id == "req_999"
    assert response.reason is None
    assert response.metadata is not None
    assert response.metadata["retrieval_count"] == 2
    assert response.metadata["model"] == "llama-3.1-8b-instant"

    # Verify retrieval called exactly once
    mock_retriever.assert_called_once_with("Who invented the Turing machine?", 2)

    # Verify generator called exactly once
    mock_generator.assert_called_once()
    gen_call_kwargs = mock_generator.call_args.kwargs
    assert gen_call_kwargs["question"] == "Who invented the Turing machine?"
    assert len(gen_call_kwargs["retrieved_chunks"]) == 2
    assert gen_call_kwargs["retrieved_chunks"][0]["chunk_id"] == "chunk_1"


def test_harness_safety_guardrail_refusal(mock_retriever, mock_generator):
    """Test that clearly unsafe input is refused and stops BEFORE retrieval and Groq."""
    harness = RAGHarness(
        retriever_fn=mock_retriever,
        generator_fn=mock_generator,
    )
    req = QueryRequest(
        query="How to make a bomb at home?",
        language="en",
        request_id="req_unsafe_1",
    )

    response = harness.run(req)

    assert response.status == ResponseStatus.REFUSED
    assert response.reason == "unsafe_content_refusal"
    assert "dangerous or harmful" in response.answer
    assert response.request_id == "req_unsafe_1"

    # Verify neither retrieval nor Groq generation were called
    mock_retriever.assert_not_called()
    mock_generator.assert_not_called()


def test_harness_hindi_safety_guardrail_refusal(mock_retriever, mock_generator):
    """Test that unsafe Hindi input is refused and stops BEFORE Groq."""
    harness = RAGHarness(
        retriever_fn=mock_retriever,
        generator_fn=mock_generator,
    )
    req = QueryRequest(
        query="बम बनाने की विधि क्या है?",
        language="hi",
        request_id="req_unsafe_hi",
    )

    response = harness.run(req)

    assert response.status == ResponseStatus.REFUSED
    assert response.reason == "unsafe_content_refusal"
    mock_retriever.assert_not_called()
    mock_generator.assert_not_called()


def test_harness_context_sufficiency_guardrail(mock_generator):
    """Test that low-similarity / irrelevant retrieval triggers general-knowledge fallback via LLM."""
    low_scoring_retriever = MagicMock()
    low_scoring_retriever.return_value = [
        {"chunk_id": "c1", "text": "unrelated content", "score": 0.22},
        {"chunk_id": "c2", "text": "random noise", "score": 0.18},
    ]

    harness = RAGHarness(
        retriever_fn=low_scoring_retriever,
        generator_fn=mock_generator,
        min_similarity_threshold=0.35,
    )
    req = QueryRequest(
        query="Who won the 2024 cricket cup?",
        language="en",
        request_id="req_offtopic",
    )

    response = harness.run(req)

    assert response.status == ResponseStatus.SUCCESS
    assert response.reason == "general_knowledge_fallback"
    assert response.request_id == "req_offtopic"

    # Verify retrieval was called once, and the generator was called for the fallback
    low_scoring_retriever.assert_called_once()
    mock_generator.assert_called_once()
    # The fallback call should include a system_prompt kwarg
    call_kwargs = mock_generator.call_args
    assert call_kwargs.kwargs.get("system_prompt") or (len(call_kwargs.args) > 6 and call_kwargs.args[6])


def test_harness_retrieval_exception_recovery(mock_generator):
    """Test that a failure in retrieval produces a controlled FinalResponse(status=ERROR)."""
    failing_retriever = MagicMock()
    failing_retriever.side_effect = RuntimeError("FAISS index unavailable")

    harness = RAGHarness(
        retriever_fn=failing_retriever,
        generator_fn=mock_generator,
    )
    req = QueryRequest(query="Some query", language="en", request_id="req_err1")

    response = harness.run(req)

    assert response.status == ResponseStatus.ERROR
    assert response.reason == "retrieval_failure"
    assert "retrieving" in response.answer.lower()
    assert response.request_id == "req_err1"
    # Ensure generator was not called
    mock_generator.assert_not_called()


def test_harness_llm_exception_recovery(mock_retriever):
    """Test that a failure in LLM generation produces a controlled FinalResponse(status=ERROR)."""
    failing_generator = MagicMock()
    failing_generator.side_effect = RuntimeError("Groq API timeout")

    harness = RAGHarness(
        retriever_fn=mock_retriever,
        generator_fn=failing_generator,
    )
    req = QueryRequest(query="Some query", language="hi", request_id="req_err2")

    response = harness.run(req)

    assert response.status == ResponseStatus.ERROR
    assert response.reason == "llm_generation_failure"
    assert "generating" in response.answer.lower()
    assert response.language == "hi"
    assert response.request_id == "req_err2"


def test_harness_empty_llm_answer(mock_retriever):
    """Test that an empty answer text from LLM produces a controlled FinalResponse(status=ERROR)."""
    empty_generator = MagicMock()
    empty_generator.return_value = {
        "answer": "   ",
        "model": "llama-3.1-8b-instant",
        "llm_latency_ms": 100.0,
    }

    harness = RAGHarness(
        retriever_fn=mock_retriever,
        generator_fn=empty_generator,
    )
    req = QueryRequest(query="Some query", request_id="req_empty")

    response = harness.run(req)

    assert response.status == ResponseStatus.ERROR
    assert response.reason == "empty_llm_answer"
    assert response.request_id == "req_empty"


def test_harness_malformed_llm_response(mock_retriever):
    """Test that non-dict or malformed LLM response produces controlled error."""
    malformed_generator = MagicMock()
    malformed_generator.return_value = "raw string instead of dict"

    harness = RAGHarness(
        retriever_fn=mock_retriever,
        generator_fn=malformed_generator,
    )
    req = QueryRequest(query="Some query")

    response = harness.run(req)

    assert response.status == ResponseStatus.ERROR
    assert response.reason == "malformed_llm_response"


def test_harness_invalid_request_recovery():
    """Test passing invalid input formats to harness."""
    harness = RAGHarness(retriever_fn=MagicMock(), generator_fn=MagicMock())

    # String auto-wrapping works
    res_str = harness.run("Valid string query")
    assert res_str.status in (ResponseStatus.SUCCESS, ResponseStatus.ERROR, ResponseStatus.INSUFFICIENT_CONTEXT)

    # Empty string in QueryRequest raises ValueError on creation
    with pytest.raises(ValueError):
        harness.run(QueryRequest(query=""))

    # Non-supported object type
    res_invalid = harness.run(12345)  # type: ignore
    assert res_invalid.status == ResponseStatus.ERROR
    assert res_invalid.reason == "invalid_request_type"


def test_harness_preserves_language_and_request_id(mock_retriever, mock_generator):
    """Test preservation of language tag and request ID in FinalResponse."""
    harness = RAGHarness(
        retriever_fn=mock_retriever,
        generator_fn=mock_generator,
    )
    req = QueryRequest(
        query="कृत्रिम बुद्धिमत्ता क्या है?",
        language="hi",
        request_id="req_hindi_42",
    )

    response = harness.run(req)

    assert response.status == ResponseStatus.SUCCESS
    assert response.language == "hi"
    assert response.request_id == "req_hindi_42"


def test_harness_grounding_failure_intercepts_hallucination(sample_raw_chunks):
    """Test that a hallucinated answer generated by LLM is caught by grounding guardrail."""
    retriever = MagicMock()
    retriever.return_value = sample_raw_chunks

    hallucinating_generator = MagicMock()
    hallucinating_generator.return_value = {
        "answer": "Alan Turing invented the Turing machine in 1999 alongside Steve Jobs in California.",
        "model": "llama-3.1-8b-instant",
        "llm_latency_ms": 130.0,
    }

    harness = RAGHarness(
        retriever_fn=retriever,
        generator_fn=hallucinating_generator,
    )
    req = QueryRequest(
        query="When did Alan Turing invent the machine?",
        language="en",
        request_id="req_hallucinated",
    )

    response = harness.run(req)

    assert response.status == ResponseStatus.SUCCESS
    assert response.reason == "general_knowledge_fallback"
    assert response.request_id == "req_hallucinated"
    assert response.metadata is not None
    assert response.metadata["grounding_reason"] == "general_knowledge_fallback"
    # Generator called twice: once for strict RAG (caught by grounding), once for fallback
    assert hallucinating_generator.call_count == 2

