from pathlib import Path

from check_results import check, percentile, summarize

FIXTURES = Path(__file__).parent / "fixtures"
THRESHOLDS = {"max_error_rate": 0.01, "p95_ms": {"default": 200, "GET /search": 300}}


def test_percentile_nearest_rank():
    assert percentile([10, 20, 30, 40, 50, 60, 70, 80, 90, 100], 95) == 100
    assert percentile([5], 95) == 5
    assert percentile([], 95) == 0


def test_summarize_counts_errors_per_label():
    stats = summarize(FIXTURES / "with_errors.jtl")
    assert stats["GET /orders (auth)"]["count"] == 3
    assert stats["GET /orders (auth)"]["errors"] == 2


def test_good_run_passes():
    assert check(summarize(FIXTURES / "good.jtl"), THRESHOLDS) == []


def test_error_rate_over_budget_fails():
    problems = check(summarize(FIXTURES / "with_errors.jtl"), THRESHOLDS)
    assert any("error rate" in p for p in problems)


def test_slow_endpoint_uses_its_own_limit():
    problems = check(summarize(FIXTURES / "slow_search.jtl"), THRESHOLDS)
    assert problems == ["GET /search: p95 450 ms > 300 ms"]


def test_empty_file_is_a_failure():
    assert check(summarize(FIXTURES / "empty.jtl"), THRESHOLDS) == ["no samples in the results file"]
