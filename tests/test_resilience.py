"""Concurrency, deduplication, partial-failure, and timeout isolation tests."""

from __future__ import annotations

import threading
import time
import pytest

from metabolic_engine import ConcurrentBatchRunner


def test_runner_validates_initialization_parameters() -> None:
    with pytest.raises(ValueError, match="max_workers"):
        ConcurrentBatchRunner(max_workers=0)

    with pytest.raises(ValueError, match="timeout_seconds"):
        ConcurrentBatchRunner(timeout_seconds=0.0)


def test_runner_handles_empty_input() -> None:
    runner = ConcurrentBatchRunner(max_workers=4, timeout_seconds=1.0)
    results, errors = runner.run([], lambda x: x)

    assert results == {}
    assert errors == {}


def test_runner_deduplicates_keys_before_dispatch() -> None:
    call_count = 0
    lock = threading.Lock()

    def worker(item: str) -> str:
        nonlocal call_count
        with lock:
            call_count += 1
        return item.upper()

    runner = ConcurrentBatchRunner(max_workers=4, timeout_seconds=1.0)
    results, errors = runner.run(["gene_a", "gene_b", "gene_a", "gene_b"], worker)

    assert call_count == 2
    assert results == {"gene_a": "GENE_A", "gene_b": "GENE_B"}
    assert errors == {}


def test_runner_isolates_partial_worker_exceptions() -> None:
    def flaky_worker(key: str) -> int:
        if key == "bad_key":
            raise RuntimeError("Upstream 503 Service Unavailable")
        return len(key)

    runner = ConcurrentBatchRunner(max_workers=3, timeout_seconds=1.0)
    results, errors = runner.run(["alpha", "bad_key", "beta"], flaky_worker)

    assert results == {"alpha": 5, "beta": 4}
    assert "bad_key" in errors
    assert "RuntimeError" in errors["bad_key"]


def test_runner_isolates_slow_worker_timeouts() -> None:
    def variable_latency_worker(key: str) -> str:
        if key == "slow_endpoint":
            time.sleep(0.25)
            return "late"
        return "fast_ok"

    runner = ConcurrentBatchRunner(max_workers=2, timeout_seconds=0.05)
    results, errors = runner.run(["fast_endpoint", "slow_endpoint"], variable_latency_worker)

    assert results == {"fast_endpoint": "fast_ok"}
    assert "slow_endpoint" in errors
    assert "Timed out" in errors["slow_endpoint"]


def test_runner_executes_tasks_in_parallel() -> None:
    def io_bound_task(key: int) -> int:
        time.sleep(0.08)
        return key * 2

    runner = ConcurrentBatchRunner(max_workers=4, timeout_seconds=1.0)
    start = time.perf_counter()
    results, errors = runner.run([1, 2, 3, 4], io_bound_task)
    elapsed = time.perf_counter() - start

    assert results == {1: 2, 2: 4, 3: 6, 4: 8}
    assert errors == {}
    # Sequential execution would take >= 0.32s; parallel execution finishes well under 0.25s
    assert elapsed < 0.25