from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any, Dict


class OrchestrationMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters = defaultdict(float)
        self._latency_totals = defaultdict(float)
        self._latency_counts = defaultdict(int)
        self._last_observed = {}

    def increment(self, key: str, value: float = 1.0) -> None:
        with self._lock:
            self._counters[key] += value

    def observe_latency(self, key: str, seconds: float) -> None:
        with self._lock:
            self._latency_totals[key] += seconds
            self._latency_counts[key] += 1
            self._last_observed[key] = seconds

    def record_event(self, key: str, metadata: Any = None) -> None:
        with self._lock:
            self._counters[key] += 1.0
            if metadata is not None:
                self._last_observed[key] = metadata

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            latency = {}
            for key, total in self._latency_totals.items():
                count = self._latency_counts.get(key, 0)
                latency[key] = {
                    "count": count,
                    "total_seconds": round(total, 6),
                    "avg_seconds": round(total / count, 6) if count else 0.0,
                    "last_seconds": round(self._last_observed.get(key, 0.0), 6) if isinstance(self._last_observed.get(key), (int, float)) else None,
                }
            return {
                "counters": dict(self._counters),
                "latency": latency,
                "last_observed": dict(self._last_observed),
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._latency_totals.clear()
            self._latency_counts.clear()
            self._last_observed.clear()


_DEFAULT_METRICS = OrchestrationMetrics()


def get_orchestration_metrics() -> OrchestrationMetrics:
    return _DEFAULT_METRICS


def timing_start() -> float:
    return time.perf_counter()
