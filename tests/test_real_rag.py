"""Unit tests for RealRAGService adapter connecting FastAPI to Stage 5 Harness."""

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.schemas.rag import RagResponse
from src.config import Language
from src.orchestration.schemas import FinalResponse, QueryRequest, ResponseStatus
from src.services.mock_rag import MockRAGService
from src.services.rag_service import (
    AudioInput,
    AudioInvalidError,
    InvalidQueryError,
    RAGService,
    SttFailedError,
    get_rag_service,
)
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


def test_real_rag_service_greeting_mapping():
    """Test mapping of greeting FinalResponse to RagResponse."""
    harness = MagicMock()
    harness.run.return_value = FinalResponse(
        answer="Hello! I am Vaani (वाणी), your AI assistant.",
        status=ResponseStatus.SUCCESS,
        reason="conversational_greeting",
        language="en",
        metadata={"is_greeting": True, "grounded": True, "sources": []},
    )
    service = RealRAGService(harness=harness)
    resp = service.query("hello")

    assert resp.grounded is True
    assert resp.confidence == 1.0
    assert resp.sources == []
    assert "Vaani" in resp.answer


def test_real_rag_service_general_knowledge_fallback_mapping():
    """Test mapping of general knowledge fallback response."""
    harness = MagicMock()
    harness.run.return_value = FinalResponse(
        answer="Climate change is primarily caused by greenhouse gas emissions.",
        status=ResponseStatus.SUCCESS,
        reason="general_knowledge_fallback",
        language="en",
        metadata={"grounded": False, "sources": []},
    )
    service = RealRAGService(harness=harness)
    resp = service.query("What causes climate change?")

    assert resp.grounded is False
    assert resp.confidence == 0.70
    assert resp.sources == []



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


# ==========================================
# STAGE 6B REAL RAG VOICE & STT INTEGRATION TESTS
# ==========================================

def test_real_rag_service_does_not_use_mock_transcribe_audio():
    """Verify RealRAGService module does not import or use mock_rag.transcribe_audio."""
    import src.services.real_rag as real_rag_module

    assert not hasattr(real_rag_module, "transcribe_audio")


def test_real_rag_voice_calls_stt_and_harness_once(mock_harness):
    """Test voice() calls STT exactly once and harness exactly once on success."""
    mock_stt = MagicMock()
    from src.services.sarvam_stt import STTResult
    mock_stt.transcribe.return_value = STTResult(
        transcript="Who invented the Turing machine?",
        language_code="en-IN",
        latency_ms=145.2,
        request_id="sarvam_test_123",
    )

    service = RealRAGService(harness=mock_harness, stt_service=mock_stt)
    audio = AudioInput(
        filename="question.wav",
        content_type="audio/wav",
        data=b"RIFF-fake-audio-bytes",
    )
    resp = service.voice(audio)

    assert isinstance(resp, RagResponse)
    assert resp.transcript == "Who invented the Turing machine?"
    assert resp.query == "Who invented the Turing machine?"
    assert resp.language == Language.EN
    assert resp.latency.stt_ms == 145.2
    assert resp.latency.retrieval_ms == 18.5
    assert resp.latency.generation_ms == 135.0
    assert resp.answer == "Alan Turing invented the Turing machine in 1936."

    # Verify STT called once with audio parameters
    mock_stt.transcribe.assert_called_once_with(
        filename="question.wav",
        content_type="audio/wav",
        audio_bytes=b"RIFF-fake-audio-bytes",
    )

    # Verify harness called once
    mock_harness.run.assert_called_once()
    call_req = mock_harness.run.call_args[0][0]
    assert isinstance(call_req, QueryRequest)
    assert call_req.query == "Who invented the Turing machine?"
    assert call_req.language == "en"


def test_real_rag_voice_hindi_language_detection(mock_harness):
    """Test Hindi transcript from STT correctly triggers Hindi language detection."""
    mock_stt = MagicMock()
    from src.services.sarvam_stt import STTResult
    mock_stt.transcribe.return_value = STTResult(
        transcript="प्रकाश संश्लेषण क्या है?",
        language_code="hi-IN",
        latency_ms=160.0,
    )

    service = RealRAGService(harness=mock_harness, stt_service=mock_stt)
    audio = AudioInput(
        filename="hindi.webm",
        content_type="audio/webm",
        data=b"webm-fake-bytes",
    )
    resp = service.voice(audio)

    assert resp.transcript == "प्रकाश संश्लेषण क्या है?"
    assert resp.language == Language.HI
    assert resp.latency.stt_ms == 160.0

    call_req = mock_harness.run.call_args[0][0]
    assert call_req.language == "hi"


def test_real_rag_voice_empty_audio_raises():
    """Test voice() with empty audio raises AudioInvalidError without calling STT or harness."""
    mock_stt = MagicMock()
    mock_harness = MagicMock()
    service = RealRAGService(harness=mock_harness, stt_service=mock_stt)

    from src.services.rag_service import AudioInvalidError
    with pytest.raises(AudioInvalidError):
        service.voice(AudioInput("empty.wav", "audio/wav", b""))

    mock_stt.transcribe.assert_not_called()
    mock_harness.run.assert_not_called()


def test_real_rag_voice_stt_failure_prevents_harness_execution():
    """Test STT failure raises SttFailedError and aborts before harness execution."""
    mock_stt = MagicMock()
    from src.services.rag_service import SttFailedError
    mock_stt.transcribe.side_effect = SttFailedError("Transcription service unavailable")

    mock_harness = MagicMock()
    service = RealRAGService(harness=mock_harness, stt_service=mock_stt)

    with pytest.raises(SttFailedError):
        service.voice(AudioInput("audio.wav", "audio/wav", b"bytes"))

    mock_stt.transcribe.assert_called_once()
    mock_harness.run.assert_not_called()


def test_real_rag_voice_empty_transcript_prevents_harness():
    """Test empty transcript from STT raises SttFailedError and aborts harness execution."""
    mock_stt = MagicMock()
    from src.services.sarvam_stt import STTResult
    from src.services.rag_service import SttFailedError
    mock_stt.transcribe.return_value = STTResult(
        transcript="   ",
        language_code=None,
        latency_ms=50.0,
    )

    mock_harness = MagicMock()
    service = RealRAGService(harness=mock_harness, stt_service=mock_stt)

    with pytest.raises(SttFailedError):
        service.voice(AudioInput("audio.wav", "audio/wav", b"bytes"))

    mock_stt.transcribe.assert_called_once()
    mock_harness.run.assert_not_called()


def test_fastapi_voice_endpoint_with_real_rag_service(mock_harness):
    """Test FastAPI /api/voice endpoint when injected with RealRAGService."""
    import io
    from src.services.sarvam_stt import STTResult

    mock_stt = MagicMock()
    mock_stt.transcribe.return_value = STTResult(
        transcript="Who invented the Turing machine?",
        language_code="en-IN",
        latency_ms=132.5,
    )

    real_service = RealRAGService(harness=mock_harness, stt_service=mock_stt)
    app.dependency_overrides[get_rag_service] = lambda: real_service

    client = TestClient(app)
    try:
        files = {"file": ("recording.webm", io.BytesIO(b"\x1a\x45\xdf\xa3webmdata"), "audio/webm")}
        response = client.post("/api/voice", files=files)
        assert response.status_code == 200
        body = response.json()
        assert body["transcript"] == "Who invented the Turing machine?"
        assert body["query"] == "Who invented the Turing machine?"
        assert body["answer"] == "Alan Turing invented the Turing machine in 1936."
        assert body["language"] == "en"
        assert body["latency"]["stt_ms"] == 132.5
        assert body["latency"]["retrieval_ms"] == 18.5
        assert body["latency"]["generation_ms"] == 135.0
        assert body["latency"]["total_ms"] > 0.0

        mock_stt.transcribe.assert_called_once()
        mock_harness.run.assert_called_once()
    finally:
        app.dependency_overrides.clear()

