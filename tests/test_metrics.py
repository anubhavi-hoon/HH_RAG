"""Unit tests for the deterministic percentile and success metrics."""

import pytest

from evaluation.metrics import (
    check_latency_target,
    percentile,
    success_stats,
    summarize,
    summarize_metrics,
)


def test_percentile_single_value():
    assert percentile([42.0], 50) == 42.0
    assert percentile([42.0], 70) == 42.0
    assert percentile([42.0], 100) == 42.0


def test_percentile_nearest_rank_multiple_values():
    values = [10.0, 20.0, 30.0, 40.0]
    assert percentile(values, 50) == 20.0
    assert percentile(values, 70) == 30.0
    assert percentile(values, 100) == 40.0


def test_percentile_ten_values_exact_ranks():
    values = [float(v) for v in range(1, 11)]
    assert percentile(values, 50) == 5.0
    assert percentile(values, 70) == 7.0
    assert percentile(values, 100) == 10.0


def test_percentile_handles_unsorted_input():
    unsorted_values = [40.0, 10.0, 30.0, 20.0]
    assert percentile(unsorted_values, 50) == 20.0
    assert percentile(unsorted_values, 70) == 30.0
    assert percentile(unsorted_values, 100) == 40.0


def test_percentile_p100_is_maximum():
    values = [5.0, 900.0, 12.0, 3.0]
    assert percentile(values, 100) == 900.0


def test_percentile_zero_and_low_percentile_clamped_to_first_rank():
    values = [10.0, 20.0, 30.0]
    assert percentile(values, 0) == 10.0
    assert percentile(values, 1) == 10.0


def test_percentile_empty_input_raises():
    with pytest.raises(ValueError):
        percentile([], 50)


@pytest.mark.parametrize("bad_p", [-1, 101])
def test_percentile_rejects_out_of_range_percentile(bad_p):
    with pytest.raises(ValueError):
        percentile([1.0], bad_p)


def test_summarize_empty_returns_none_not_zero():
    summary = summarize([])
    assert summary.to_dict() == {"count": 0, "p50": None, "p70": None, "p100": None}


def test_summarize_rounds_to_two_decimals():
    summary = summarize([1.23456, 2.34567, 3.45678])
    assert summary.count == 3
    assert summary.p50 == 2.35
    assert summary.p100 == 3.46


def test_summarize_metrics_covers_all_latency_fields():
    result = summarize_metrics({"client_total_ms": [10.0, 20.0]})
    assert set(result) == {
        "client_total_ms",
        "server_total_ms",
        "stt_ms",
        "embedding_ms",
        "retrieval_ms",
        "generation_ms",
        "guardrail_ms",
    }
    assert result["client_total_ms"]["p100"] == 20.0
    assert result["retrieval_ms"]["count"] == 0


def test_success_stats():
    stats = success_stats([True, True, False, True])
    assert stats.total_requests == 4
    assert stats.successful_requests == 3
    assert stats.failed_requests == 1
    assert stats.success_rate == 0.75


def test_success_stats_empty():
    stats = success_stats([])
    assert stats.total_requests == 0
    assert stats.success_rate == 0.0


def test_latency_target_pass_only_when_below_threshold():
    assert check_latency_target(184.0).status == "PASS"
    assert check_latency_target(231.0).status == "ABOVE TARGET"
    # Exactly at the target is not below it.
    assert check_latency_target(200.0).status == "ABOVE TARGET"


def test_latency_target_without_measurement():
    check = check_latency_target(None)
    assert check.status == "NOT MEASURED"
    assert check.measured_p100_ms is None


def test_latency_target_documents_what_it_measured():
    assert check_latency_target(10.0).measured_against == "client_total_ms"
