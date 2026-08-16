"""Contract tests for the FastAPI layer backed by the mock RAG service."""

import io

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.config import SERVICE_NAME, SERVICE_VERSION, SUPPORTED_LANGUAGES

client = TestClient(app)

LATENCY_KEYS = {
    "stt_ms",
    "embedding_ms",
    "retrieval_ms",
    "generation_ms",
    "guardrail_ms",
    "total_ms",
}
RESPONSE_KEYS = {
    "transcript",
    "query",
    "language",
    "answer",
    "grounded",
    "confidence",
    "sources",
    "latency",
}
SOURCE_KEYS = {"chunk_id", "text", "score", "language", "strategy", "doc_id"}


def assert_error_envelope(response, expected_code: str) -> None:
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == expected_code
    assert body["error"]["message"]
    assert "Traceback" not in body["error"]["message"]


# ==========================================
# Health
# ==========================================

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }


# ==========================================
# Query
# ==========================================

def test_query_returns_full_contract():
    response = client.post("/api/query", json={"query": "What is photosynthesis?"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == RESPONSE_KEYS
    assert set(body["latency"]) == LATENCY_KEYS
    assert body["transcript"] is None
    assert body["query"] == "What is photosynthesis?"
    assert body["language"] in SUPPORTED_LANGUAGES
    assert body["grounded"] is True
    assert 0.0 <= body["confidence"] <= 1.0
    assert len(body["sources"]) > 0


def test_query_source_schema_matches_canonical_contract():
    body = client.post("/api/query", json={"query": "What is photosynthesis?"}).json()
    for source in body["sources"]:
        assert set(source) == SOURCE_KEYS
        assert isinstance(source["chunk_id"], str)
        assert isinstance(source["text"], str)
        assert 0.0 <= source["score"] <= 1.0
        assert source["language"] in SUPPORTED_LANGUAGES
        assert source["strategy"] is None or isinstance(source["strategy"], str)


def test_query_returns_source_with_and_without_strategy():
    body = client.post("/api/query", json={"query": "What is photosynthesis?"}).json()
    strategies = [source["strategy"] for source in body["sources"]]
    assert any(isinstance(value, str) and value for value in strategies)
    assert any(value is None for value in strategies)


def test_query_hindi_detected():
    response = client.post("/api/query", json={"query": "प्रकाश संश्लेषण क्या है?"})
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "hi"
    assert body["grounded"] is True


def test_query_is_deterministic():
    payload = {"query": "What is photosynthesis?"}
    first = client.post("/api/query", json=payload).json()
    second = client.post("/api/query", json=payload).json()
    # Latency is a real measurement and therefore varies; everything else must not.
    first.pop("latency")
    second.pop("latency")
    assert first == second


def test_query_unknown_topic_is_not_grounded():
    response = client.post("/api/query", json={"query": "quarterly revenue of acme"})
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["sources"] == []


@pytest.mark.parametrize("payload", [{"query": ""}, {"query": "   "}, {}])
def test_query_invalid_payloads_return_invalid_query_error(payload):
    response = client.post("/api/query", json=payload)
    assert response.status_code == 422
    assert_error_envelope(response, "INVALID_QUERY")


def test_query_malformed_body_returns_error_envelope():
    response = client.post(
        "/api/query",
        content=b"{not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert_error_envelope(response, "INVALID_QUERY")


def test_query_wrong_type_returns_error_envelope():
    response = client.post("/api/query", json={"query": 42})
    assert response.status_code == 422
    assert_error_envelope(response, "INVALID_QUERY")


# ==========================================
# Voice
# ==========================================

def test_voice_returns_mock_transcript():
    files = {"file": ("sample.wav", io.BytesIO(b"RIFF-fake-audio"), "audio/wav")}
    response = client.post("/api/voice", files=files)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == RESPONSE_KEYS
    assert set(body["latency"]) == LATENCY_KEYS
    assert body["transcript"]
    assert body["query"] == body["transcript"]


def test_voice_reports_zero_stt_because_no_transcription_happens():
    files = {"file": ("sample.wav", io.BytesIO(b"RIFF-fake-audio"), "audio/wav")}
    latency = client.post("/api/voice", files=files).json()["latency"]
    assert latency["stt_ms"] == 0
    assert latency["total_ms"] >= 0


def test_voice_empty_file_rejected():
    files = {"file": ("empty.wav", io.BytesIO(b""), "audio/wav")}
    response = client.post("/api/voice", files=files)
    assert response.status_code == 422
    assert_error_envelope(response, "AUDIO_INVALID")


def test_voice_missing_file_rejected():
    response = client.post("/api/voice")
    assert response.status_code == 422
    assert_error_envelope(response, "AUDIO_INVALID")


def test_voice_rejects_non_audio_content_type():
    files = {"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")}
    response = client.post("/api/voice", files=files)
    assert response.status_code == 415
    assert_error_envelope(response, "AUDIO_INVALID")


# ==========================================
# Request correlation & error contract
# ==========================================

def test_request_id_is_generated_when_absent():
    response = client.get("/api/health")
    request_id = response.headers.get("X-Request-ID")
    assert request_id
    assert len(request_id) >= 8


def test_request_id_is_echoed_when_supplied():
    response = client.post(
        "/api/query",
        json={"query": "What is photosynthesis?"},
        headers={"X-Request-ID": "bench-run-42"},
    )
    assert response.headers.get("X-Request-ID") == "bench-run-42"


def test_request_id_present_on_error_responses():
    response = client.post("/api/query", json={"query": ""})
    assert response.status_code == 422
    assert response.headers.get("X-Request-ID")


def test_unknown_route_returns_error_envelope():
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert_error_envelope(response, "NOT_FOUND")


def test_service_failure_maps_to_error_envelope(monkeypatch):
    from src.services import mock_rag
    from src.services.rag_service import RetrievalFailedError

    def boom(*_args, **_kwargs):
        raise RetrievalFailedError("Unable to retrieve relevant context.")

    monkeypatch.setattr(mock_rag.MockRAGService, "query", boom)
    response = client.post("/api/query", json={"query": "What is photosynthesis?"})

    assert response.status_code == 503
    assert_error_envelope(response, "RETRIEVAL_FAILED")
    assert response.json()["error"]["message"] == "Unable to retrieve relevant context."


def test_unexpected_exception_does_not_leak_internals(monkeypatch):
    from src.services import mock_rag

    def boom(*_args, **_kwargs):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(mock_rag.MockRAGService, "query", boom)
    response = client.post("/api/query", json={"query": "photosynthesis"})

    assert response.status_code == 500
    assert_error_envelope(response, "INTERNAL_ERROR")
    assert "secret internal detail" not in response.text
