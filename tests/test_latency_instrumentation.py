"""Latency instrumentation tests.

These assert the *shape* of the measurement (real, non-negative, not a sum of
stages), never a specific duration, so they cannot become flaky on slow machines.
"""

import io
import time

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.services import mock_rag
from src.services.mock_rag import MockRAGService
from src.services.rag_service import AudioInput
from src.utils.timing import Timer

client = TestClient(app)

STAGE_KEYS = (
    "stt_ms",
    "embedding_ms",
    "retrieval_ms",
    "generation_ms",
    "guardrail_ms",
)


# ==========================================
# Timer utility
# ==========================================

def test_timer_measures_elapsed_milliseconds():
    with Timer() as timer:
        time.sleep(0.01)
    assert timer.elapsed_ms >= 10.0


def test_timer_freezes_after_stop():
    timer = Timer().start()
    time.sleep(0.005)
    stopped = timer.stop()
    time.sleep(0.005)
    assert timer.elapsed_ms == stopped


def test_timer_rejects_stop_before_start():
    with pytest.raises(RuntimeError):
        Timer().stop()


# ==========================================
# Mock service reports no simulated latency
# ==========================================

def test_deterministic_jitter_is_gone():
    assert not hasattr(mock_rag, "_deterministic_jitter")
    assert not hasattr(mock_rag, "_build_latency")


def test_mock_service_reports_zero_for_every_stage():
    latency = MockRAGService().query("What is photosynthesis?").latency
    for key in STAGE_KEYS:
        assert getattr(latency, key) == 0


def test_mock_voice_reports_zero_stt_regardless_of_filename():
    service = MockRAGService()
    first = service.voice(AudioInput("a.webm", "audio/webm", b"xxxx"))
    second = service.voice(AudioInput("completely-different.wav", "audio/wav", b"y"))
    assert first.latency.stt_ms == 0
    assert second.latency.stt_ms == 0


def test_service_does_not_set_total_ms_itself():
    # total_ms is owned by the API layer, which measures the call.
    assert MockRAGService().query("What is photosynthesis?").latency.total_ms == 0


# ==========================================
# total_ms is wall clock, measured by the API layer
# ==========================================

@pytest.mark.parametrize("path", ["/api/query", "/api/voice"])
def test_total_ms_is_measured_wall_clock(path):
    if path == "/api/query":
        body = client.post(path, json={"query": "What is photosynthesis?"}).json()
    else:
        files = {"file": ("sample.wav", io.BytesIO(b"RIFF-fake-audio"), "audio/wav")}
        body = client.post(path, files=files).json()

    latency = body["latency"]
    assert latency["total_ms"] >= 0
    # Real execution of the service always consumes measurable time.
    assert latency["total_ms"] > 0


def test_total_ms_is_not_the_sum_of_stages():
    latency = client.post("/api/query", json={"query": "What is photosynthesis?"}).json()[
        "latency"
    ]
    stage_sum = sum(latency[key] for key in STAGE_KEYS)
    assert stage_sum == 0
    assert latency["total_ms"] != stage_sum


def test_total_ms_varies_between_identical_requests():
    payload = {"query": "What is photosynthesis?"}
    totals = {
        client.post("/api/query", json=payload).json()["latency"]["total_ms"]
        for _ in range(8)
    }
    # A hash-derived constant would collapse to a single value.
    assert len(totals) > 1


def test_process_time_header_is_reported():
    response = client.post("/api/query", json={"query": "What is photosynthesis?"})
    header = response.headers.get("X-Process-Time-Ms")
    assert header is not None
    process_ms = float(header)
    body_total = response.json()["latency"]["total_ms"]
    # Full request handling wraps the service call it contains.
    assert process_ms >= body_total
