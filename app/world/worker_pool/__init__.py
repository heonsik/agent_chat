from __future__ import annotations

from collections import deque
import time
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional

from app.world.job_runner import JobRunner


class WorkerPool:
    def __init__(self, job_runner: JobRunner) -> None:
        self._queue: Deque[Dict[str, Any]] = deque()
        self._job_runner = job_runner

    def submit(self, job_id: str, todos: Iterable[Dict[str, Any]]) -> None:
        self._queue.append({"job_id": job_id, "todos": list(todos)})

    def fetch_job(self) -> Optional[Dict[str, Any]]:
        if not self._queue:
            return None
        return self._queue.popleft()

    def run_next(self) -> Optional[Dict[str, Any]]:
        job = self.fetch_job()
        if job is None:
            return None
        return self._job_runner.run_job(job["job_id"], job["todos"])

    def run_until_empty(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        while self._queue:
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


__all__ = ["WorkerPool"]
