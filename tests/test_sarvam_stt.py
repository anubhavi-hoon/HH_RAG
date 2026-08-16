"""
Unit tests for SarvamSTTService.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pytest

from src.services.rag_service import AudioInvalidError, SttFailedError
from src.services.sarvam_stt import (
    DEFAULT_LANGUAGE_CODE,
    DEFAULT_SARVAM_MODE,
    DEFAULT_SARVAM_MODEL,
    STTResult,
    SarvamSTTService,
)


@pytest.fixture
def mock_sarvam_client():
    """Mock SarvamAI client with speech_to_text attribute."""
    client = MagicMock()
    return client


def test_stt_result_creation():
    """Verify STTResult dataclass fields and behavior."""
    res = STTResult(
        transcript="What is machine learning?",
        language_code="en-IN",
        latency_ms=120.5,
        request_id="req_abc123",
    )
    assert res.transcript == "What is machine learning?"
    assert res.language_code == "en-IN"
    assert res.latency_ms == 120.5
    assert res.request_id == "req_abc123"


def test_sarvam_stt_english_success(mock_sarvam_client):
    """Test successful English transcription."""
    mock_sarvam_client.speech_to_text.transcribe.return_value = SimpleNamespace(
        transcript="What is artificial intelligence?",
        language_code="en-IN",
        request_id="req_en_01",
    )

    service = SarvamSTTService(client=mock_sarvam_client)
    result = service.transcribe(
        filename="audio.wav",
        content_type="audio/wav",
        audio_bytes=b"RIFF\x00\x00fakeaudio",
    )

    assert isinstance(result, STTResult)
    assert result.transcript == "What is artificial intelligence?"
    assert result.language_code == "en-IN"
    assert result.request_id == "req_en_01"
    assert result.latency_ms >= 0.0

    mock_sarvam_client.speech_to_text.transcribe.assert_called_once()
    kwargs = mock_sarvam_client.speech_to_text.transcribe.call_args[1]
    assert kwargs["model"] == "saaras:v3"
    assert kwargs["mode"] == "transcribe"
    assert kwargs["language_code"] == "unknown"
    assert kwargs["file"] == ("audio.wav", b"RIFF\x00\x00fakeaudio", "audio/wav")


def test_sarvam_stt_hindi_success(mock_sarvam_client):
    """Test successful Hindi transcription."""
    mock_sarvam_client.speech_to_text.transcribe.return_value = SimpleNamespace(
        transcript="प्रकाश संश्लेषण क्या है?",
        language_code="hi-IN",
        request_id="req_hi_01",
    )

    service = SarvamSTTService(client=mock_sarvam_client)
    result = service.transcribe(
        filename="hindi_rec.webm",
        content_type="audio/webm",
        audio_bytes=b"\x1a\x45\xdf\xa3fakeaudio",
    )

    assert isinstance(result, STTResult)
    assert result.transcript == "प्रकाश संश्लेषण क्या है?"
    assert result.language_code == "hi-IN"
    assert result.request_id == "req_hi_01"
    assert result.latency_ms >= 0.0


def test_sarvam_stt_whitespace_trimming(mock_sarvam_client):
    """Test leading/trailing whitespace in transcript is trimmed."""
    mock_sarvam_client.speech_to_text.transcribe.return_value = SimpleNamespace(
        transcript="   What is Goa famous for?   \n\t ",
        language_code="en-IN",
        request_id="req_trim",
    )

    service = SarvamSTTService(client=mock_sarvam_client)
    result = service.transcribe(
        filename="rec.webm",
        content_type="audio/webm",
        audio_bytes=b"dummy",
    )
    assert result.transcript == "What is Goa famous for?"


def test_sarvam_stt_empty_audio_raises():
    """Test empty audio bytes raises AudioInvalidError without calling API."""
    client = MagicMock()
    service = SarvamSTTService(client=client)

    with pytest.raises(AudioInvalidError) as exc_info:
        service.transcribe("empty.wav", "audio/wav", b"")
    assert "empty" in str(exc_info.value).lower()
    client.speech_to_text.transcribe.assert_not_called()


def test_sarvam_stt_empty_transcript_raises(mock_sarvam_client):
    """Test provider returning empty/whitespace transcript raises SttFailedError."""
    mock_sarvam_client.speech_to_text.transcribe.return_value = SimpleNamespace(
        transcript="   \t\n  ",
        language_code=None,
        request_id="req_empty",
    )

    service = SarvamSTTService(client=mock_sarvam_client)
    with pytest.raises(SttFailedError) as exc_info:
        service.transcribe("rec.webm", "audio/webm", b"dummy")
    assert "empty transcript" in str(exc_info.value).lower()


def test_sarvam_stt_missing_api_key_raises(monkeypatch):
    """Test missing SARVAM_API_KEY environment variable raises SttFailedError."""
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    service = SarvamSTTService(api_key=None, client=None)

    with pytest.raises(SttFailedError) as exc_info:
        service.transcribe("rec.webm", "audio/webm", b"dummy_audio")
    assert "SARVAM_API_KEY is not configured" in str(exc_info.value)


def test_sarvam_stt_provider_error_handling(mock_sarvam_client):
    """Test provider exceptions are caught and wrapped in SttFailedError."""
    mock_sarvam_client.speech_to_text.transcribe.side_effect = RuntimeError("Connection dropped")

    service = SarvamSTTService(client=mock_sarvam_client)
    with pytest.raises(SttFailedError) as exc_info:
        service.transcribe("rec.webm", "audio/webm", b"dummy_audio")
    assert "Speech-to-text transcription failed" in str(exc_info.value)


def test_sarvam_stt_timeout_handling(mock_sarvam_client):
    """Test timeout exception is cleanly wrapped in SttFailedError."""
    mock_sarvam_client.speech_to_text.transcribe.side_effect = TimeoutError("Request timed out")

    service = SarvamSTTService(client=mock_sarvam_client)
    with pytest.raises(SttFailedError) as exc_info:
        service.transcribe("rec.webm", "audio/webm", b"dummy_audio")
    assert "Speech-to-text transcription failed" in str(exc_info.value)


def test_sarvam_stt_never_logs_api_key(caplog, monkeypatch):
    """Test API keys are never exposed in logs or exception messages."""
    secret_key = "sk_secret_sarvam_key_99999"
    service = SarvamSTTService(api_key=secret_key, client=None)

    with patch("sarvamai.SarvamAI", side_effect=Exception("Initialization failure")):
        with pytest.raises(SttFailedError) as exc_info:
            service.transcribe("rec.webm", "audio/webm", b"dummy")

        assert secret_key not in str(exc_info.value)
        for record in caplog.records:
            assert secret_key not in record.message


def test_sarvam_stt_configuration_defaults():
    """Verify default STT parameters match modern Sarvam guidelines."""
    assert DEFAULT_SARVAM_MODEL == "saaras:v3"
    assert DEFAULT_SARVAM_MODE == "transcribe"
    assert DEFAULT_LANGUAGE_CODE == "unknown"

    service = SarvamSTTService()
    assert service.model == "saaras:v3"
    assert service.mode == "transcribe"
    assert service.language_code == "unknown"


def test_sarvam_stt_none_response_raises(mock_sarvam_client):
    """Test provider returning None raises SttFailedError."""
    mock_sarvam_client.speech_to_text.transcribe.return_value = None

    service = SarvamSTTService(client=mock_sarvam_client)
    with pytest.raises(SttFailedError) as exc_info:
        service.transcribe("rec.webm", "audio/webm", b"dummy")
    assert "empty response" in str(exc_info.value).lower()
