#!/usr/bin/env python3
"""Latency benchmark runner for the HH_RAG API.

Sends every query in a benchmark set to ``POST /api/query`` and records two
independent latencies:

* ``client_total_ms`` - measured here with :func:`time.perf_counter`, from just
  before the request is sent until the response body has been read. This is the
  user-facing number and the one the 200 ms target is judged against.
* server-reported values from the response ``latency`` block - ``total_ms`` is the
  backend's own wall clock for the service call; the stage fields are individual
  operation durations and are ``0`` when a stage did not run.

Latency values are never synthesised: failed requests are recorded as failures and
excluded from the percentile samples.

Text and voice are benchmarked as separate pipelines and their results are never
merged, because voice additionally carries STT latency.

Usage:
    python evaluation/benchmark.py --limit 50
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

if __package__ in (None, ""):  # allow `python evaluation/benchmark.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.metrics import (  # noqa: E402
    LATENCY_FIELDS,
    LATENCY_TARGET_MS,
    check_latency_target,
    success_stats,
    summarize_metrics,
)

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_INPUT = Path(__file__).resolve().parent / "queries.json"
DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_DELAY_S = 0.05
DEFAULT_TIMEOUT_S = 30.0
QUERY_ENDPOINT = "/api/query"
VOICE_ENDPOINT = "/api/voice"
REQUEST_ID_HEADER = "X-Request-ID"
PROCESS_TIME_HEADER = "X-Process-Time-Ms"

#: Pipelines are reported separately; voice includes STT, text does not.
PIPELINE_TEXT = "text"
PIPELINE_VOICE = "voice"


class BenchmarkRequestError(Exception):
    """A single API request failed; the run continues with the next query."""


@dataclass(frozen=True)
class ApiResponse:
    """Decoded API response plus correlation and timing headers."""

    payload: Dict[str, Any]
    request_id: Optional[str] = None
    server_process_ms: Optional[float] = None


@dataclass(frozen=True)
class QueryCase:
    """One benchmark input loaded from the query set."""

    id: str
    query: str
    language: str
    expected_behavior: str


@dataclass
class QueryResult:
    """Measured outcome of a single benchmark request.

    ``client_total_ms`` is measured by this script. Every other latency field is
    reported by the server and copied verbatim.
    """

    query_id: str
    query: str
    language: str
    expected_behavior: str
    success: bool
    client_total_ms: float
    pipeline: str = PIPELINE_TEXT
    server_total_ms: Optional[float] = None
    server_process_ms: Optional[float] = None
    stt_ms: Optional[float] = None
    embedding_ms: Optional[float] = None
    retrieval_ms: Optional[float] = None
    generation_ms: Optional[float] = None
    guardrail_ms: Optional[float] = None
    grounded: Optional[bool] = None
    confidence: Optional[float] = None
    source_count: Optional[int] = None
    detected_language: Optional[str] = None
    request_id: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ==========================================
# Query set loading
# ==========================================

def load_queries(path: Path, limit: Optional[int] = None) -> List[QueryCase]:
    """Load and validate the benchmark query set."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Query file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Query file is not valid JSON: {path} ({exc})") from exc

    if not isinstance(raw, list):
        raise SystemExit(f"Query file must contain a JSON array: {path}")

    cases: List[QueryCase] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or not str(item.get("query", "")).strip():
            raise SystemExit(f"Query entry {index} is missing a non-empty 'query'")
        cases.append(
            QueryCase(
                id=str(item.get("id") or f"q{index + 1:03d}"),
                query=str(item["query"]),
                language=str(item.get("language", "unknown")),
                expected_behavior=str(item.get("expected_behavior", "unspecified")),
            )
        )

    if limit is not None and limit >= 0:
        cases = cases[:limit]
    if not cases:
        raise SystemExit("No queries to benchmark")
    return cases


# ==========================================
# HTTP transport
# ==========================================

def _error_detail(body: str) -> str:
    """Extract `{"error": {"code", "message"}}` when the API sends its envelope."""
    try:
        decoded = json.loads(body)
    except json.JSONDecodeError:
        return body[:200]

    envelope = decoded.get("error") if isinstance(decoded, dict) else None
    if isinstance(envelope, dict):
        return f"{envelope.get('code', 'UNKNOWN')}: {envelope.get('message', '')}".strip()
    return body[:200]


def post_json(
    base_url: str,
    endpoint: str,
    payload: Dict[str, Any],
    timeout: float,
) -> ApiResponse:
    """POST a JSON body and return the decoded response.

    Kept endpoint-agnostic so a future /api/voice benchmark can reuse it.
    """
    request = urllib.request.Request(
        url=f"{base_url.rstrip('/')}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            request_id = response.headers.get(REQUEST_ID_HEADER)
            process_ms = _as_float(response.headers.get(PROCESS_TIME_HEADER))
    except urllib.error.HTTPError as exc:
        detail = _error_detail(exc.read().decode("utf-8", errors="replace"))
        raise BenchmarkRequestError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise BenchmarkRequestError(f"connection failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise BenchmarkRequestError(f"request timed out after {timeout}s") from exc

    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as exc:
        raise BenchmarkRequestError(f"malformed JSON response: {exc}") from exc

    if not isinstance(decoded, dict):
        raise BenchmarkRequestError("response body was not a JSON object")
    return ApiResponse(
        payload=decoded,
        request_id=request_id,
        server_process_ms=process_ms,
    )


def _as_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


# ==========================================
# Measurement
# ==========================================

def _latency_value(latency: Any, key: str) -> Optional[float]:
    if not isinstance(latency, dict):
        return None
    value = latency.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def run_query(
    base_url: str,
    case: QueryCase,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> QueryResult:
    """Execute one benchmark request, measuring client-side round-trip latency."""
    # The clock starts immediately before the request and stops once the full
    # response body has been read. Nothing else is included.
    started = time.perf_counter()
    try:
        api_response = post_json(base_url, QUERY_ENDPOINT, {"query": case.query}, timeout)
    except BenchmarkRequestError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return QueryResult(
            query_id=case.id,
            query=case.query,
            language=case.language,
            expected_behavior=case.expected_behavior,
            success=False,
            client_total_ms=round(elapsed_ms, 2),
            error=str(exc),
        )
    elapsed_ms = (time.perf_counter() - started) * 1000

    response = api_response.payload
    latency = response.get("latency")
    sources = response.get("sources")
    confidence = response.get("confidence")

    return QueryResult(
        query_id=case.id,
        query=case.query,
        language=case.language,
        expected_behavior=case.expected_behavior,
        success=True,
        client_total_ms=round(elapsed_ms, 2),
        pipeline=PIPELINE_TEXT,
        server_total_ms=_latency_value(latency, "total_ms"),
        server_process_ms=api_response.server_process_ms,
        stt_ms=_latency_value(latency, "stt_ms"),
        embedding_ms=_latency_value(latency, "embedding_ms"),
        retrieval_ms=_latency_value(latency, "retrieval_ms"),
        generation_ms=_latency_value(latency, "generation_ms"),
        guardrail_ms=_latency_value(latency, "guardrail_ms"),
        grounded=response.get("grounded") if isinstance(response.get("grounded"), bool) else None,
        confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
        source_count=len(sources) if isinstance(sources, list) else None,
        detected_language=response.get("language") if isinstance(response.get("language"), str) else None,
        request_id=api_response.request_id,
    )


def run_benchmark(
    cases: Sequence[QueryCase],
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = DEFAULT_TIMEOUT_S,
    delay: float = DEFAULT_DELAY_S,
    log: bool = True,
) -> List[QueryResult]:
    """Run every case in order. A failing request never aborts the run."""
    results: List[QueryResult] = []
    total = len(cases)

    for index, case in enumerate(cases, start=1):
        result = run_query(base_url, case, timeout=timeout)
        results.append(result)

        if log:
            outcome = (
                f"{result.client_total_ms:8.2f} ms"
                if result.success
                else f"FAILED ({result.error})"
            )
            print(f"[{index:3d}/{total}] {result.query_id}  {outcome}", file=sys.stderr)

        if delay > 0 and index < total:
            time.sleep(delay)

    return results


# ==========================================
# Reporting
# ==========================================

def collect_samples(results: Sequence[QueryResult]) -> Dict[str, List[float]]:
    """Gather latency samples from successful requests only."""
    samples: Dict[str, List[float]] = {field: [] for field in LATENCY_FIELDS}
    for result in results:
        if not result.success:
            continue
        for field in LATENCY_FIELDS:
            value = getattr(result, field, None)
            if isinstance(value, (int, float)):
                samples[field].append(float(value))
    return samples


def build_report(
    results: Sequence[QueryResult],
    base_url: str,
    input_path: Path,
    started_at: datetime,
    pipeline: str = PIPELINE_TEXT,
) -> Dict[str, Any]:
    """Assemble the JSON report: metadata, summary and per-query records."""
    samples = collect_samples(results)
    summary = summarize_metrics(samples)
    stats = success_stats([result.success for result in results])
    # The target is a user-facing claim, so it is judged on client round trip.
    target = check_latency_target(summary["client_total_ms"]["p100"], LATENCY_TARGET_MS)

    return {
        "metadata": {
            "timestamp": started_at.isoformat(),
            "base_url": base_url,
            "endpoint": QUERY_ENDPOINT if pipeline == PIPELINE_TEXT else VOICE_ENDPOINT,
            "pipeline": pipeline,
            "input_file": str(input_path),
            "query_count": len(results),
        },
        "summary": {
            **summary,
            "requests": stats.to_dict(),
            "latency_target": target.to_dict(),
        },
        "queries": [result.to_dict() for result in results],
    }


def _format_block(title: str, block: Dict[str, Optional[float]]) -> str:
    def value(key: str) -> str:
        raw = block.get(key)
        return f"{raw:.2f} ms" if isinstance(raw, (int, float)) else "n/a"

    lines = [title, "-" * len(title)]
    lines.append(f"P50:  {value('p50')}")
    lines.append(f"P70:  {value('p70')}")
    lines.append(f"P100: {value('p100')}")
    return "\n".join(lines)


STAGE_FIELDS = ("stt_ms", "embedding_ms", "retrieval_ms", "generation_ms", "guardrail_ms")


def _any_stage_measured(summary: Dict[str, Any]) -> bool:
    """True when at least one pipeline stage reported non-zero work."""
    return any(
        isinstance(summary.get(field, {}).get("p100"), (int, float))
        and summary[field]["p100"] > 0
        for field in STAGE_FIELDS
    )


def render_report(report: Dict[str, Any]) -> str:
    """Render the human-readable benchmark summary."""
    meta = report["metadata"]
    summary = report["summary"]
    stats = summary["requests"]
    target = summary["latency_target"]
    pipeline_title = f"{meta['pipeline'].upper()} PIPELINE"

    sections = [
        "HH_RAG Benchmark",
        "================",
        "",
        pipeline_title,
        "-" * len(pipeline_title),
        f"Endpoint:     {meta['base_url']}{meta['endpoint']}",
        f"Queries:      {stats['total_requests']}",
        f"Successful:   {stats['successful_requests']}",
        f"Failed:       {stats['failed_requests']}",
        f"Success rate: {stats['success_rate'] * 100:.1f}%",
        "",
        "Client total = HTTP round trip measured by this script (user-facing).",
        "Server total = backend wall clock for the service call (subset of the above).",
        "Stages       = individual operations; 'n/a' means the stage did not run.",
        "",
        _format_block("Client Total Latency", summary["client_total_ms"]),
        "",
        _format_block("Server Total Latency", summary["server_total_ms"]),
        "",
        "Stage Latencies",
        "---------------",
        _format_block("STT", summary["stt_ms"]),
        "",
        _format_block("Embedding", summary["embedding_ms"]),
        "",
        _format_block("Retrieval", summary["retrieval_ms"]),
        "",
        _format_block("Generation", summary["generation_ms"]),
        "",
        _format_block("Guardrails", summary["guardrail_ms"]),
        "",
        f"Latency target: <{target['target_ms']:.0f}ms (measured against client round trip)",
    ]

    measured = target["measured_p100_ms"]
    sections.append(
        f"Client P100: {measured:.2f}ms"
        if isinstance(measured, (int, float))
        else "Client P100: n/a"
    )
    sections.append(f"Status: {target['status']}")

    if not _any_stage_measured(summary):
        sections += [
            "",
            "NOTE: no pipeline stage reported measurable work, so this run exercised",
            "      HTTP and framework overhead only. It says nothing about whether the",
            "      integrated retrieval + generation system will meet the target.",
        ]
    return "\n".join(sections)


def resolve_output_path(output: Optional[Path], started_at: datetime) -> Path:
    """Return a unique output path; existing benchmark files are never overwritten."""
    if output is not None:
        path = output
    else:
        stamp = started_at.strftime("%Y-%m-%dT%H%M%S")
        path = DEFAULT_RESULTS_DIR / f"benchmark_{stamp}.json"

    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return path

    for suffix in range(2, 1000):
        candidate = path.with_name(f"{path.stem}_{suffix}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise SystemExit(f"Could not find a free filename next to {path}")


def save_report(report: Dict[str, Any], path: Path) -> Path:
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ==========================================
# CLI
# ==========================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark HH_RAG /api/query latency (P50/P70/P100).",
    )
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Query set JSON")
    parser.add_argument("--output", type=Path, default=None, help="Result file path")
    parser.add_argument("--limit", type=int, default=None, help="Max queries to run")
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_S,
        help="Delay between requests in seconds",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_S,
        help="Per-request timeout in seconds",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    cases = load_queries(args.input, args.limit)

    started_at = datetime.now(timezone.utc)
    results = run_benchmark(
        cases,
        base_url=args.url,
        timeout=args.timeout,
        delay=args.delay,
    )

    report = build_report(results, args.url, args.input, started_at, PIPELINE_TEXT)
    output_path = save_report(report, resolve_output_path(args.output, started_at))

    print()
    print(render_report(report))
    print()
    print(f"Raw results: {output_path}")

    return 0 if report["summary"]["requests"]["failed_requests"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
