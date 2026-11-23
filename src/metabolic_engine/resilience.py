"""Fault-tolerant concurrent task orchestrator with per-worker timeout isolation."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, wait
from typing import TypeVar

K = TypeVar("K")
V = TypeVar("V")


class ConcurrentBatchRunner:
    """Executes I/O-bound tasks in parallel with isolated failure and timeout handling."""

    def __init__(self, max_workers: int = 10, timeout_seconds: float = 10.0) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds

    def run(
        self,
        keys: Iterable[K],
        worker_fn: Callable[[K], V],
    ) -> tuple[dict[K, V], dict[K, str]]:
        """Runs worker_fn across deduplicated keys, isolating failures per worker."""
        unique_keys = list(dict.fromkeys(keys))
        results: dict[K, V] = {}
        errors: dict[K, str] = {}

        if not unique_keys:
            return results, errors

        executor = ThreadPoolExecutor(max_workers=self.max_workers)
        try:
            future_map = {executor.submit(worker_fn, key): key for key in unique_keys}
            done, not_done = wait(future_map.keys(), timeout=self.timeout_seconds)

            for future in done:
                key = future_map[future]
                try:
                    results[key] = future.result()
                except Exception as exc:  # noqa: BLE001
                    errors[key] = f"{type(exc).__name__}: {exc}"

            for future in not_done:
                key = future_map[future]
                future.cancel()
                errors[key] = f"Worker timed out after {self.timeout_seconds}s"
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        return results, errors