from __future__ import annotations

import queue
import time
from typing import Any, Callable, Dict, Iterable, List, Optional

from app.world.job_runner import JobRunner


class WorkerPool:
    def __init__(self, job_runner: JobRunner, event_bus=None) -> None:
        self._queue: queue.Queue[Dict[str, Any]] = queue.Queue()
        self._job_runner = job_runner
        self._event_bus = event_bus

    def submit(self, job_id: str, todos: Iterable[Dict[str, Any]] | None) -> None:
        self._queue.put({"job_id": job_id, "todos": list(todos or [])})
        self._emit_queue()

    def fetch_job(self) -> Optional[Dict[str, Any]]:
        try:
            job = self._queue.get_nowait()
        except queue.Empty:
            return None
        self._emit_queue()
        return job

    def run_next(self) -> Optional[Dict[str, Any]]:
        job = self.fetch_job()
        if job is None:
            return None
        return self._job_runner.run_job(job["job_id"], job["todos"])

    def run_until_empty(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        while not self._queue.empty():
            result = self.run_next()
            if result is not None:
                results.append(result)
        return results

    def run_loop(self, stop_flag: Callable[[], bool], idle_sleep_s: float = 0.05) -> None:
        while not stop_flag():
            result = self.run_next()
            if result is None:
                time.sleep(idle_sleep_s)
                continue

    def _emit_queue(self) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            "queue_state",
            {"queued": self._queue.qsize()},
        )


__all__ = ["WorkerPool"]
