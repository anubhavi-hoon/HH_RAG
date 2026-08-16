"""Deterministic latency statistics for the HH_RAG benchmark.

Percentiles use the **nearest-rank** method (no interpolation), so every reported
value is a measurement that was actually observed:

    rank  = ceil(p / 100 * n)   clamped to [1, n]
    value = sorted(values)[rank - 1]

Consequences:
    * P100 is always the maximum observed value.
    * P50 of [10, 20, 30, 40] is 20 (rank 2), not the interpolated median 25.
    * Re-running the same measurements always yields the same percentiles.

Only the standard library is used.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional, Sequence

#: Task 2 end-to-end latency target, in milliseconds. It is evaluated against
#: *client* round-trip latency, because that is what a user actually waits for.
LATENCY_TARGET_MS: float = 200.0

#: Percentiles reported by the benchmark.
REPORTED_PERCENTILES: tuple[int, ...] = (50, 70, 100)

#: Latency fields summarised for every benchmark run.
LATENCY_FIELDS: tuple[str, ...] = (
    "client_total_ms",
    "server_total_ms",
    "stt_ms",
    "embedding_ms",
    "retrieval_ms",
    "generation_ms",
    "guardrail_ms",
)


def percentile(values: Sequence[float], p: float) -> float:
    """Return the nearest-rank ``p``-th percentile of ``values``.

    Raises:
        ValueError: if ``values`` is empty or ``p`` is outside [0, 100].
    """
    if not values:
        raise ValueError("percentile() requires at least one value")
    if not 0 <= p <= 100:
        raise ValueError(f"percentile p must be within [0, 100], got {p}")

    ordered = sorted(values)
    n = len(ordered)
    # Multiply before dividing so integral percentiles stay exact in binary float.
    rank = math.ceil(round((p * n) / 100, 9))
    rank = min(max(rank, 1), n)
    return ordered[rank - 1]


@dataclass(frozen=True)
class PercentileSummary:
    """Percentile block for a single latency metric.

    Percentiles are ``None`` when no samples were collected, so that an empty or
    fully failed run is never reported as a latency of zero.
    """

    count: int
    p50: Optional[float]
    p70: Optional[float]
    p100: Optional[float]

    def to_dict(self) -> Dict[str, Optional[float]]:
        return asdict(self)


def summarize(values: Iterable[float]) -> PercentileSummary:
    """Build a P50/P70/P100 summary, tolerating an empty sample set."""
    samples: List[float] = [float(v) for v in values if v is not None]
    if not samples:
        return PercentileSummary(count=0, p50=None, p70=None, p100=None)
    return PercentileSummary(
        count=len(samples),
        p50=round(percentile(samples, 50), 2),
        p70=round(percentile(samples, 70), 2),
        p100=round(percentile(samples, 100), 2),
    )


@dataclass(frozen=True)
class SuccessStats:
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


def success_stats(successes: Sequence[bool]) -> SuccessStats:
    """Count successful/failed requests and the resulting success rate."""
    total = len(successes)
    successful = sum(1 for ok in successes if ok)
    rate = round(successful / total, 4) if total else 0.0
    return SuccessStats(
        total_requests=total,
        successful_requests=successful,
        failed_requests=total - successful,
        success_rate=rate,
    )


@dataclass(frozen=True)
class TargetCheck:
    """Outcome of comparing measured client-side P100 against the latency target."""

    target_ms: float
    measured_p100_ms: Optional[float]
    status: str
    measured_against: str = "client_total_ms"

    def to_dict(self) -> Dict[str, Optional[float]]:
        return asdict(self)


def check_latency_target(
    measured_p100_ms: Optional[float],
    target_ms: float = LATENCY_TARGET_MS,
) -> TargetCheck:
    """Report PASS only when a real measurement is strictly below the target."""
    if measured_p100_ms is None:
        status = "NOT MEASURED"
    elif measured_p100_ms < target_ms:
        status = "PASS"
    else:
        status = "ABOVE TARGET"
    return TargetCheck(
        target_ms=target_ms,
        measured_p100_ms=measured_p100_ms,
        status=status,
    )


def summarize_metrics(
    samples_by_field: Dict[str, Sequence[float]],
) -> Dict[str, Dict[str, Optional[float]]]:
    """Summarise every latency field in :data:`LATENCY_FIELDS`."""
    return {
        field: summarize(samples_by_field.get(field, [])).to_dict()
        for field in LATENCY_FIELDS
    }
