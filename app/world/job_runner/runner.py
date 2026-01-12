from __future__ import annotations

from typing import Any, Dict, Iterable

from app.world.adapter.tool_runtime_adapter import ToolRuntimeAdapter, ToolRuntimeResult
from app.world.job_manager import JobManager
from app.world.types import JobState


def run_single_todo(todo: Dict[str, Any], adapter: ToolRuntimeAdapter) -> ToolRuntimeResult:
    return adapter.run(todo)


class JobRunner:
    def __init__(
        self,
        job_manager: JobManager,
        adapter: ToolRuntimeAdapter,
    ) -> None:
        self._job_manager = job_manager
        self._adapter = adapter

    def run_job(self, job_id: str, todos: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        self._job_manager.update_state(job_id, JobState.RUNNING)
        for index, todo in enumerate(todos):
            if self._job_manager.is_canceled(job_id):
                self._job_manager.append_log(job_id, f"todo[{index}] canceled")
                self._job_manager.update_state(job_id, JobState.CANCELED)
                return {"status": "canceled"}
            result = run_single_todo(todo, self._adapter)
            status = result.state
            if status == "waiting_lock":
                reason = result.reason
                self._job_manager.append_log(job_id, f"todo[{index}] locked: {reason}")
                self._job_manager.update_state(job_id, JobState.WAITING_LOCK)
                return {"status": "waiting_lock", "reason": reason}
            if status == "waiting_confirm":
                self._job_manager.append_log(job_id, f"todo[{index}] waiting_confirm")
                self._job_manager.update_state(job_id, JobState.WAITING_CONFIRM)
                return {"status": "waiting_confirm"}
            if status == "failed":
                error = result.error
                self._job_manager.append_log(job_id, f"todo[{index}] failed: {error}")
                self._job_manager.update_state(job_id, JobState.FAILED)
                self._job_manager.set_result(job_id, {"error": error}, state=JobState.FAILED)
                return {"status": "failed", "error": error}
            self._job_manager.append_log(job_id, f"todo[{index}] done")

        self._job_manager.set_result(job_id, {"status": "done"}, state=JobState.DONE)
        return {"status": "done"}
