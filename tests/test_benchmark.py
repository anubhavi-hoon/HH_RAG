"""Tests for the benchmark runner: query loading, failure resilience, reporting."""

import json
from datetime import datetime, timezone

import pytest

from evaluation import benchmark
from evaluation.benchmark import (
    ApiResponse,
    BenchmarkRequestError,
    QueryCase,
    QueryResult,
    build_report,
    collect_samples,
    load_queries,
    resolve_output_path,
    run_benchmark,
)

MOCK_RESPONSE = {
    "transcript": None,
    "query": "What is photosynthesis?",
    "language": "en",
    "answer": "…",
    "grounded": True,
    "confidence": 0.93,
    "sources": [{"chunk_id": "c1"}],
    "latency": {
        "stt_ms": 0,
        "embedding_ms": 0,
        "retrieval_ms": 0,
        "generation_ms": 0,
        "guardrail_ms": 0,
        "total_ms": 0.42,
    },
}

MOCK_API_RESPONSE = ApiResponse(
    payload=MOCK_RESPONSE, request_id="req-123", server_process_ms=1.5
)


def make_cases(count: int):
    return [
        QueryCase(
            id=f"q{index:03d}",
            query=f"question {index}",
            language="en",
            expected_behavior="answer",
        )
        for index in range(1, count + 1)
    ]


def test_load_queries_applies_limit(tmp_path):
    path = tmp_path / "queries.json"
    path.write_text(
        json.dumps(
            [
                {"id": "q001", "query": "a", "language": "en", "expected_behavior": "answer"},
                {"id": "q002", "query": "b", "language": "hi", "expected_behavior": "refuse"},
            ]
        ),
        encoding="utf-8",
    )

    cases = load_queries(path, limit=1)
    assert len(cases) == 1
    assert cases[0].id == "q001"


def test_load_queries_rejects_blank_query(tmp_path):
    path = tmp_path / "queries.json"
    path.write_text(json.dumps([{"id": "q001", "query": "   "}]), encoding="utf-8")
    with pytest.raises(SystemExit):
        load_queries(path)


def test_bundled_query_set_is_valid():
    cases = load_queries(benchmark.DEFAULT_INPUT)
    assert len(cases) >= 50
    assert len({case.id for case in cases}) == len(cases)
    assert {case.language for case in cases} <= {"en", "hi"}
    assert {case.expected_behavior for case in cases} <= {"answer", "refuse"}


def test_failed_request_does_not_terminate_benchmark(monkeypatch):
    calls = {"n": 0}

    def fake_post_json(base_url, endpoint, payload, timeout):
        calls["n"] += 1
        if calls["n"] == 2:
            raise BenchmarkRequestError("connection failed: refused")
        return MOCK_API_RESPONSE

    monkeypatch.setattr(benchmark, "post_json", fake_post_json)

    results = run_benchmark(make_cases(4), delay=0, log=False)

    assert len(results) == 4
    assert calls["n"] == 4
    assert [r.success for r in results] == [True, False, True, True]
    assert results[1].error == "connection failed: refused"
    assert results[1].server_total_ms is None


def test_failed_requests_are_excluded_from_latency_samples(monkeypatch):
    def always_fail(base_url, endpoint, payload, timeout):
        raise BenchmarkRequestError("HTTP 500: boom")

    monkeypatch.setattr(benchmark, "post_json", always_fail)
    results = run_benchmark(make_cases(3), delay=0, log=False)

    samples = collect_samples(results)
    assert samples["server_total_ms"] == []
    assert samples["client_total_ms"] == []

    report = build_report(results, "http://localhost:8000", benchmark.DEFAULT_INPUT, datetime.now(timezone.utc))
    assert report["summary"]["requests"]["failed_requests"] == 3
    assert report["summary"]["server_total_ms"]["p100"] is None
    assert report["summary"]["latency_target"]["status"] == "NOT MEASURED"


def test_build_report_uses_server_reported_latency(monkeypatch):
    monkeypatch.setattr(
        benchmark, "post_json", lambda *_args, **_kwargs: MOCK_API_RESPONSE
    )
    results = run_benchmark(make_cases(2), delay=0, log=False)
    report = build_report(results, "http://localhost:8000", benchmark.DEFAULT_INPUT, datetime.now(timezone.utc))

    assert report["metadata"]["query_count"] == 2
    assert report["summary"]["server_total_ms"]["p100"] == 0.42
    assert report["summary"]["retrieval_ms"]["p50"] == 0.0
    assert len(report["queries"]) == 2
    assert report["queries"][0]["grounded"] is True


def test_client_latency_is_measured_independently_of_the_server(monkeypatch):
    monkeypatch.setattr(
        benchmark, "post_json", lambda *_args, **_kwargs: MOCK_API_RESPONSE
    )
    result = run_benchmark(make_cases(1), delay=0, log=False)[0]

    # Client latency comes from this process's own clock, not the response body.
    assert result.client_total_ms >= 0
    assert result.server_total_ms == 0.42
    assert result.server_process_ms == 1.5


def test_latency_target_is_evaluated_against_client_p100():
    fast = [_result_with_client_ms(ms) for ms in (10.0, 20.0, 30.0)]
    slow = [_result_with_client_ms(ms) for ms in (10.0, 20.0, 500.0)]

    fast_target = _target_of(fast)
    slow_target = _target_of(slow)

    assert fast_target["measured_against"] == "client_total_ms"
    assert fast_target["measured_p100_ms"] == 30.0
    assert fast_target["status"] == "PASS"
    # P100 is the max client value, not the server value.
    assert slow_target["measured_p100_ms"] == 500.0
    assert slow_target["status"] == "ABOVE TARGET"


def _result_with_client_ms(client_ms: float) -> QueryResult:
    return QueryResult(
        query_id="q",
        query="q",
        language="en",
        expected_behavior="answer",
        success=True,
        client_total_ms=client_ms,
        server_total_ms=0.4,
    )


def _target_of(results):
    report = build_report(
        results, "http://localhost:8000", benchmark.DEFAULT_INPUT, datetime.now(timezone.utc)
    )
    return report["summary"]["latency_target"]


def test_text_and_voice_pipelines_are_reported_separately():
    results = [_result_with_client_ms(10.0)]
    started = datetime.now(timezone.utc)

    text = build_report(results, "http://x", benchmark.DEFAULT_INPUT, started, benchmark.PIPELINE_TEXT)
    voice = build_report(results, "http://x", benchmark.DEFAULT_INPUT, started, benchmark.PIPELINE_VOICE)

    assert text["metadata"]["pipeline"] == "text"
    assert text["metadata"]["endpoint"] == benchmark.QUERY_ENDPOINT
    assert voice["metadata"]["pipeline"] == "voice"
    assert voice["metadata"]["endpoint"] == benchmark.VOICE_ENDPOINT
    assert "TEXT PIPELINE" in benchmark.render_report(text)
    assert "VOICE PIPELINE" in benchmark.render_report(voice)


def test_request_id_is_recorded(monkeypatch):
    monkeypatch.setattr(
        benchmark, "post_json", lambda *_args, **_kwargs: MOCK_API_RESPONSE
    )
    results = run_benchmark(make_cases(1), delay=0, log=False)
    assert results[0].request_id == "req-123"


def test_resolve_output_path_does_not_overwrite(tmp_path):
    started = datetime.now(timezone.utc)
    first = tmp_path / "benchmark.json"
    first.write_text("{}", encoding="utf-8")

    second = resolve_output_path(first, started)
    assert second != first
    assert not second.exists()
