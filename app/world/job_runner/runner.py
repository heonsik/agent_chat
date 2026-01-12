from __future__ import annotations

from typing import Any, Dict, Iterable

from app.world.adapter.tool_runtime_adapter import ToolRuntimeAdapter, ToolRuntimeResult
from app.world.job_manager import JobManager
from app.world.types import JobState


def run_single_todo(
    todo: Dict[str, Any],
    adapter: ToolRuntimeAdapter,
    skip_confirm: bool = False,
) -> ToolRuntimeResult:
    return adapter.run(todo, skip_confirm=skip_confirm)


class JobRunner:
    def __init__(
        self,
        job_manager: JobManager,
        adapter: ToolRuntimeAdapter,
    ) -> None:
        self._job_manager = job_manager
        self._adapter = adapter
        self._pending_confirm: Dict[str, Dict[str, Any]] = {}

    def run_job(self, job_id: str, todos: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        todos_list = list(todos)
        return self._run_todos(job_id, todos_list, start_index=0)

    def resume_confirm(self, job_id: str, approved: bool) -> Dict[str, Any]:
        pending = self._pending_confirm.pop(job_id, None)
        if pending is None:
            return {"status": "no_pending"}
        if not approved:
            self._job_manager.update_state(job_id, JobState.CANCELED)
            self._job_manager.append_log(job_id, "confirm rejected")
            return {"status": "canceled"}
        todo = pending["todo"]
        remaining = pending["remaining"]
        result = run_single_todo(todo, self._adapter, skip_confirm=True)
        if result.state == "failed":
            error = result.error
            self._job_manager.append_log(job_id, f"todo failed: {error}")
            self._job_manager.update_state(job_id, JobState.FAILED)
            self._job_manager.set_result(job_id, {"error": error}, state=JobState.FAILED)
            return {"status": "failed", "error": error}
        if result.state == "waiting_lock":
            self._job_manager.update_state(job_id, JobState.WAITING_LOCK)
            return {"status": "waiting_lock", "reason": result.reason}
        return self._run_todos(job_id, remaining, start_index=0)

    def _run_todos(
        self,
        job_id: str,
        todos: list[Dict[str, Any]],
        start_index: int,
    ) -> Dict[str, Any]:
        self._job_manager.update_state(job_id, JobState.RUNNING)
        for index, todo in enumerate(todos[start_index:], start=start_index):
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
                self._pending_confirm[job_id] = {
                    "todo": todo,
                    "remaining": todos[index + 1 :],
                }
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
