"""Tests for the RAGService abstraction and its mock implementation."""

import pytest

from src.api.schemas.rag import RagResponse
from src.config import Language
from src.services.mock_rag import MockRAGService
from src.services.rag_service import (
    AudioInput,
    ErrorCode,
    InvalidQueryError,
    RAGService,
    RagServiceError,
    get_rag_service,
)


def test_mock_implements_the_interface():
    assert issubclass(MockRAGService, RAGService)
    assert isinstance(get_rag_service(), RAGService)


def test_interface_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        RAGService()  # type: ignore[abstract]


def test_query_returns_rag_response():
    response = MockRAGService().query("What is photosynthesis?")
    assert isinstance(response, RagResponse)
    assert response.language is Language.EN
    assert response.grounded is True


def test_query_detects_hindi():
    response = MockRAGService().query("प्रकाश संश्लेषण क्या है?")
    assert response.language is Language.HI


@pytest.mark.parametrize("bad_query", ["", "   "])
def test_query_rejects_blank_input(bad_query):
    with pytest.raises(InvalidQueryError) as exc_info:
        MockRAGService().query(bad_query)
    assert exc_info.value.code is ErrorCode.INVALID_QUERY
    assert exc_info.value.status_code == 422


def test_voice_produces_transcript():
    audio = AudioInput(filename="clip.webm", content_type="audio/webm", data=b"binary")
    response = MockRAGService().voice(audio)
    assert response.transcript
    assert response.query == response.transcript
    # The mock performs no transcription, so it must not claim STT latency.
    assert response.latency.stt_ms == 0


def test_service_errors_carry_code_and_status():
    error = RagServiceError("something failed")
    assert error.code is ErrorCode.INTERNAL_ERROR
    assert error.status_code == 500
    assert str(error) == "something failed"


def test_sources_may_omit_strategy():
    sources = MockRAGService().query("What is photosynthesis?").sources
    assert any(source.strategy is None for source in sources)
    assert any(source.strategy for source in sources)
