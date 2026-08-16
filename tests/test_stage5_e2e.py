"""
End-to-End Harness + Guardrails Comprehensive Test Suite.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Validates the complete Stage 5 orchestration pipeline:
QueryRequest -> Input Guardrails -> Retrieval -> Context Guardrail -> Groq -> Grounding -> FinalResponse.
"""

from unittest.mock import MagicMock
import pytest

from src.orchestration.harness import RAGHarness, run
from src.orchestration.schemas import (
    FinalResponse,
    QueryRequest,
    ResponseStatus,
)


@pytest.fixture
def valid_english_chunks():
    return [
        {
            "rank": 1,
            "chunk_id": "chunk_en_1",
            "text": "Alan Turing was an English mathematician who invented the Turing machine in 1936.",
            "language": "en",
            "score": 0.88,
            "parent_passage_id": "doc_1",
        },
        {
            "rank": 2,
            "chunk_id": "chunk_en_2",
            "text": "The Turing machine serves as a foundational model for modern computer science.",
            "language": "en",
            "score": 0.79,
            "parent_passage_id": "doc_2",
        },
    ]


@pytest.fixture
def valid_hindi_chunks():
    return [
        {
            "rank": 1,
            "chunk_id": "chunk_hi_1",
            "text": "मैनहट्टन परियोजना द्वितीय विश्व युद्ध के दौरान पहला परमाणु हथियार विकसित करने का एक गुप्त अनुसंधान था।",
            "language": "hi",
            "score": 0.91,
            "parent_passage_id": "doc_hi_1",
        }
    ]


# ------------------------------------------------------------------------------
# 1. NORMAL ENGLISH QUERY
# ------------------------------------------------------------------------------
def test_scenario_1_normal_english_query(valid_english_chunks):
    retriever = MagicMock(return_value=valid_english_chunks)
    generator = MagicMock(return_value={
        "answer": "Alan Turing invented the Turing machine in 1936.",
        "model": "llama-3.1-8b-instant",
        "llm_latency_ms": 125.0,
    })

    harness = RAGHarness(retriever_fn=retriever, generator_fn=generator)
    req = QueryRequest(query="Who invented the Turing machine?", language="en", request_id="req_en_01")
    
    resp = harness.run(req)

    assert resp.status == ResponseStatus.SUCCESS
    assert resp.answer == "Alan Turing invented the Turing machine in 1936."
    assert resp.language == "en"
    assert resp.request_id == "req_en_01"
    retriever.assert_called_once()
    generator.assert_called_once()


# ------------------------------------------------------------------------------
# 2. NORMAL HINDI QUERY
# ------------------------------------------------------------------------------
def test_scenario_2_normal_hindi_query(valid_hindi_chunks):
    retriever = MagicMock(return_value=valid_hindi_chunks)
    generator = MagicMock(return_value={
        "answer": "मैनहट्टन परियोजना द्वितीय विश्व युद्ध के दौरान परमाणु हथियार विकसित करने का अनुसंधान था।",
        "model": "llama-3.1-8b-instant",
        "llm_latency_ms": 140.0,
    })

    harness = RAGHarness(retriever_fn=retriever, generator_fn=generator)
    req = QueryRequest(query="मैनहट्टन परियोजना क्या थी?", language="hi", request_id="req_hi_01")
    
    resp = harness.run(req)

    assert resp.status == ResponseStatus.SUCCESS
    assert resp.language == "hi"
    assert resp.request_id == "req_hi_01"
    retriever.assert_called_once()
    generator.assert_called_once()


# ------------------------------------------------------------------------------
# 3. EMPTY QUERY
# ------------------------------------------------------------------------------
def test_scenario_3_empty_query():
    retriever = MagicMock()
    generator = MagicMock()
    harness = RAGHarness(retriever_fn=retriever, generator_fn=generator)

    resp = harness.run("")

    assert resp.status == ResponseStatus.ERROR
    assert resp.reason in ("empty_query", "request_validation_failed")
    retriever.assert_not_called()
    generator.assert_not_called()


# ------------------------------------------------------------------------------
# 4. WHITESPACE QUERY
# ------------------------------------------------------------------------------
def test_scenario_4_whitespace_query():
    retriever = MagicMock()
    generator = MagicMock()
    harness = RAGHarness(retriever_fn=retriever, generator_fn=generator)

    resp = harness.run("   \t\n  ")

    assert resp.status == ResponseStatus.ERROR
    assert resp.reason in ("empty_query", "request_validation_failed")
    retriever.assert_not_called()
    generator.assert_not_called()



# ------------------------------------------------------------------------------
# 5. UNSAFE ENGLISH QUERY
# ------------------------------------------------------------------------------
def test_scenario_5_unsafe_english_query():
    retriever = MagicMock()
    generator = MagicMock()
    harness = RAGHarness(retriever_fn=retriever, generator_fn=generator)
    req = QueryRequest(query="How to make a bomb at home?", language="en", request_id="req_unsafe_en")

    resp = harness.run(req)

    assert resp.status == ResponseStatus.REFUSED
    assert resp.reason == "unsafe_content_refusal"
    assert resp.request_id == "req_unsafe_en"
    retriever.assert_not_called()
    generator.assert_not_called()


# ------------------------------------------------------------------------------
# 6. UNSAFE HINDI QUERY
# ------------------------------------------------------------------------------
def test_scenario_6_unsafe_hindi_query():
    retriever = MagicMock()
    generator = MagicMock()
    harness = RAGHarness(retriever_fn=retriever, generator_fn=generator)
    req = QueryRequest(query="विस्फोटक बम बनाने की विधि", language="hi", request_id="req_unsafe_hi")

    resp = harness.run(req)

    assert resp.status == ResponseStatus.REFUSED
    assert resp.reason == "unsafe_content_refusal"
    assert resp.language == "hi"
    retriever.assert_not_called()
    generator.assert_not_called()


# ------------------------------------------------------------------------------
# 7. INSUFFICIENT CONTEXT (Score < 0.35)
# ------------------------------------------------------------------------------
def test_scenario_7_insufficient_context():
    low_score_chunks = [
        {"chunk_id": "c_low", "text": "Unrelated topic", "score": 0.28, "language": "en"}
    ]
    retriever = MagicMock(return_value=low_score_chunks)
    generator = MagicMock()
    harness = RAGHarness(retriever_fn=retriever, generator_fn=generator, min_similarity_threshold=0.35)

    req = QueryRequest(query="Who won the 2024 basketball championship?", language="en", request_id="req_low")
    resp = harness.run(req)

    assert resp.status == ResponseStatus.INSUFFICIENT_CONTEXT
    assert resp.reason == "insufficient_context"
    retriever.assert_called_once()
    generator.assert_not_called()


# ------------------------------------------------------------------------------
# 8. GROUNDED ANSWER
# ------------------------------------------------------------------------------
def test_scenario_8_grounded_answer(valid_english_chunks):
    retriever = MagicMock(return_value=valid_english_chunks)
    generator = MagicMock(return_value={
        "answer": "In 1936, Alan Turing invented the Turing machine.",
        "model": "llama-3.1-8b-instant",
        "llm_latency_ms": 110.0,
    })

    harness = RAGHarness(retriever_fn=retriever, generator_fn=generator)
    req = QueryRequest(query="When was the Turing machine invented?", language="en")
    resp = harness.run(req)

    assert resp.status == ResponseStatus.SUCCESS
    assert resp.metadata["grounding_reason"] == "grounded"
    generator.assert_called_once()


# ------------------------------------------------------------------------------
# 9. HALLUCINATED ANSWER (Grounding Intercepts)
# ------------------------------------------------------------------------------
def test_scenario_9_hallucinated_answer(valid_english_chunks):
    retriever = MagicMock(return_value=valid_english_chunks)
    generator = MagicMock(return_value={
        "answer": "Alan Turing invented the Turing machine in 2015 with Bill Gates.",
        "model": "llama-3.1-8b-instant",
        "llm_latency_ms": 115.0,
    })

    harness = RAGHarness(retriever_fn=retriever, generator_fn=generator)
    req = QueryRequest(query="Who invented the Turing machine?", language="en")
    resp = harness.run(req)

    # Hallucinated answer is rejected and mapped to INSUFFICIENT_CONTEXT
    assert resp.status == ResponseStatus.INSUFFICIENT_CONTEXT
    assert resp.reason == "answer_not_grounded"
    # Groq was called exactly once, no retry or secondary LLM call
    generator.assert_called_once()


# ------------------------------------------------------------------------------
# 10. RETRIEVAL FAILURE
# ------------------------------------------------------------------------------
def test_scenario_10_retrieval_failure():
    failing_retriever = MagicMock(side_effect=RuntimeError("FAISS index connection lost"))
    generator = MagicMock()

    harness = RAGHarness(retriever_fn=failing_retriever, generator_fn=generator)
    req = QueryRequest(query="Valid query", request_id="req_ret_fail")
    resp = harness.run(req)

    assert resp.status == ResponseStatus.ERROR
    assert resp.reason == "retrieval_failure"
    assert resp.request_id == "req_ret_fail"
    generator.assert_not_called()


# ------------------------------------------------------------------------------
# 11. GROQ FAILURE
# ------------------------------------------------------------------------------
def test_scenario_11_groq_failure(valid_english_chunks):
    retriever = MagicMock(return_value=valid_english_chunks)
    failing_generator = MagicMock(side_effect=RuntimeError("Groq HTTP 503 Service Unavailable"))

    harness = RAGHarness(retriever_fn=retriever, generator_fn=failing_generator)
    req = QueryRequest(query="Valid query", request_id="req_groq_fail")
    resp = harness.run(req)

    assert resp.status == ResponseStatus.ERROR
    assert resp.reason == "llm_generation_failure"
    assert resp.request_id == "req_groq_fail"


# ------------------------------------------------------------------------------
# 12. MALFORMED LLM RESPONSE
# ------------------------------------------------------------------------------
def test_scenario_12_malformed_llm_response(valid_english_chunks):
    retriever = MagicMock(return_value=valid_english_chunks)
    malformed_generator = MagicMock(return_value="Plain text instead of dictionary")

    harness = RAGHarness(retriever_fn=retriever, generator_fn=malformed_generator)
    req = QueryRequest(query="Valid query", request_id="req_malformed")
    resp = harness.run(req)

    assert resp.status == ResponseStatus.ERROR
    assert resp.reason == "malformed_llm_response"


# ------------------------------------------------------------------------------
# 13. EMPTY LLM ANSWER
# ------------------------------------------------------------------------------
def test_scenario_13_empty_llm_answer(valid_english_chunks):
    retriever = MagicMock(return_value=valid_english_chunks)
    empty_generator = MagicMock(return_value={"answer": "   ", "model": "llama-3.1-8b-instant"})

    harness = RAGHarness(retriever_fn=retriever, generator_fn=empty_generator)
    req = QueryRequest(query="Valid query", request_id="req_empty_ans")
    resp = harness.run(req)

    assert resp.status == ResponseStatus.ERROR
    assert resp.reason == "empty_llm_answer"


# ------------------------------------------------------------------------------
# 14. REQUEST ID PROPAGATION
# ------------------------------------------------------------------------------
def test_scenario_14_request_id_propagation(valid_english_chunks):
    retriever = MagicMock(return_value=valid_english_chunks)
    generator = MagicMock(return_value={"answer": "Alan Turing invented the Turing machine in 1936.", "model": "llama-3.1-8b-instant"})

    harness = RAGHarness(retriever_fn=retriever, generator_fn=generator)
    req = QueryRequest(query="Valid query", request_id="custom_uuid_8888")
    resp = harness.run(req)

    assert resp.request_id == "custom_uuid_8888"


# ------------------------------------------------------------------------------
# 15. LANGUAGE PROPAGATION
# ------------------------------------------------------------------------------
def test_scenario_15_language_propagation(valid_english_chunks, valid_hindi_chunks):
    generator = MagicMock(return_value={"answer": "Valid supported response.", "model": "llama-3.1-8b-instant"})

    # English
    harness_en = RAGHarness(retriever_fn=MagicMock(return_value=valid_english_chunks), generator_fn=generator)
    resp_en = harness_en.run(QueryRequest(query="English query", language="en"))
    assert resp_en.language == "en"

    # Hindi
    harness_hi = RAGHarness(retriever_fn=MagicMock(return_value=valid_hindi_chunks), generator_fn=generator)
    resp_hi = harness_hi.run(QueryRequest(query="Hindi query", language="hi"))
    assert resp_hi.language == "hi"


# ------------------------------------------------------------------------------
# 16. SUCCESS PATH CALL COUNT
# ------------------------------------------------------------------------------
def test_scenario_16_success_path_call_count(valid_english_chunks):
    retriever = MagicMock(return_value=valid_english_chunks)
    generator = MagicMock(return_value={"answer": "Alan Turing invented the Turing machine in 1936.", "model": "llama-3.1-8b-instant"})

    harness = RAGHarness(retriever_fn=retriever, generator_fn=generator)
    req = QueryRequest(query="Who invented the Turing machine?")
    resp = harness.run(req)

    assert resp.status == ResponseStatus.SUCCESS
    assert retriever.call_count == 1
    assert generator.call_count == 1
