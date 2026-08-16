"""Unit tests for RealRAGService adapter connecting FastAPI to Stage 5 Harness."""

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.schemas.rag import RagResponse
from src.config import Language
from src.orchestration.schemas import FinalResponse, QueryRequest, ResponseStatus
from src.services.mock_rag import MockRAGService
from src.services.rag_service import InvalidQueryError, RAGService, get_rag_service
from src.services.real_rag import RealRAGService, detect_language


@pytest.fixture
def mock_harness():
    harness = MagicMock()
    harness.run.return_value = FinalResponse(
        answer="Alan Turing invented the Turing machine in 1936.",
        status=ResponseStatus.SUCCESS,
        reason=None,
        language="en",
        request_id="test_req_123",
        metadata={
            "retrieval_count": 3,
            "retrieval_latency_ms": 18.5,
            "llm_latency_ms": 135.0,
            "total_latency_ms": 154.0,
            "model": "llama-3.1-8b-instant",
        },
    )
    return harness


def test_real_rag_service_implements_interface():
    """Verify RealRAGService subclasses the abstract RAGService."""
    assert issubclass(RealRAGService, RAGService)
    service = RealRAGService(harness=MagicMock())
    assert isinstance(service, RAGService)


def test_mock_rag_service_remains_available():
    """Verify MockRAGService remains available and unchanged."""
    assert issubclass(MockRAGService, RAGService)
    mock_service = MockRAGService()
    resp = mock_service.query("What is photosynthesis?")
    assert isinstance(resp, RagResponse)
    assert resp.grounded is True


def test_real_rag_service_creates_query_request_and_calls_harness_once(mock_harness):
    """Test RealRAGService formats QueryRequest and executes harness exactly once."""
    service = RealRAGService(harness=mock_harness)
    resp = service.query("Who invented the Turing machine?")

    assert isinstance(resp, RagResponse)
    assert resp.answer == "Alan Turing invented the Turing machine in 1936."
    assert resp.language == Language.EN
    assert resp.grounded is True
    assert resp.confidence == 0.95
    assert resp.latency.retrieval_ms == 18.5
    assert resp.latency.generation_ms == 135.0
    assert resp.sources == []

    # Verify harness.run was called exactly once with QueryRequest
    mock_harness.run.assert_called_once()
    call_args = mock_harness.run.call_args[0]
    req = call_args[0]
    assert isinstance(req, QueryRequest)
    assert req.query == "Who invented the Turing machine?"
    assert req.language == "en"


def test_real_rag_service_hindi_detection(mock_harness):
    """Test Hindi script detection and language propagation."""
    service = RealRAGService(harness=mock_harness)
    resp = service.query("मैनहट्टन परियोजना क्या थी?")

    assert resp.language == Language.HI
    call_args = mock_harness.run.call_args[0]
    req = call_args[0]
    assert req.language == "hi"


def test_real_rag_service_refused_response_mapping():
    """Test mapping of a REFUSED FinalResponse to RagResponse."""
    harness = MagicMock()
    harness.run.return_value = FinalResponse(
        answer="I cannot fulfill this request as it involves dangerous content.",
        status=ResponseStatus.REFUSED,
        reason="unsafe_content_refusal",
        language="en",
    )
    service = RealRAGService(harness=harness)
    resp = service.query("How to make explosives?")

    assert resp.grounded is False
    assert resp.confidence == 0.0
    assert "dangerous" in resp.answer.lower()


def test_real_rag_service_insufficient_context_mapping():
    """Test mapping of INSUFFICIENT_CONTEXT FinalResponse to RagResponse."""
    harness = MagicMock()
    harness.run.return_value = FinalResponse(
        answer="The available context does not contain sufficient support.",
        status=ResponseStatus.INSUFFICIENT_CONTEXT,
        reason="insufficient_context",
        language="en",
    )
    service = RealRAGService(harness=harness)
    resp = service.query("Who won the 2024 championship?")

    assert resp.grounded is False
    assert resp.confidence == 0.0
    assert "sufficient" in resp.answer.lower()


def test_real_rag_service_error_response_mapping():
    """Test mapping of ERROR FinalResponse to RagResponse."""
    harness = MagicMock()
    harness.run.return_value = FinalResponse(
        answer="An error occurred while processing the request.",
        status=ResponseStatus.ERROR,
        reason="retrieval_failure",
        language="en",
    )
    service = RealRAGService(harness=harness)
    resp = service.query("Sample query")

    assert resp.grounded is False
    assert resp.confidence == 0.0


def test_real_rag_service_empty_query_raises():
    """Test empty/whitespace queries raise InvalidQueryError immediately."""
    service = RealRAGService(harness=MagicMock())
    with pytest.raises(InvalidQueryError):
        service.query("")
    with pytest.raises(InvalidQueryError):
        service.query("   \n\t  ")


def test_fastapi_endpoint_with_real_rag_service(mock_harness):
    """Test FastAPI /api/query endpoint when injected with RealRAGService."""
    real_service = RealRAGService(harness=mock_harness)
    app.dependency_overrides[get_rag_service] = lambda: real_service

    client = TestClient(app)
    try:
        response = client.post("/api/query", json={"query": "Who invented the Turing machine?"})
        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == "Alan Turing invented the Turing machine in 1936."
        assert body["grounded"] is True
        assert body["language"] == "en"
        assert body["latency"]["retrieval_ms"] == 18.5
        assert body["latency"]["generation_ms"] == 135.0
        assert body["latency"]["total_ms"] > 0.0
        mock_harness.run.assert_called_once()
    finally:
        app.dependency_overrides.clear()
