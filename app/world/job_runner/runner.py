from __future__ import annotations

from typing import Any, Dict, Iterable

from app.world.adapter.tool_runtime_adapter import ToolRuntimeAdapter, ToolRuntimeResult
from app.world.deep_agent.runner import DeepAgentRunner, extract_summary, extract_subagent_calls
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
        deep_agent_runner: DeepAgentRunner | None = None,
    ) -> None:
        self._job_manager = job_manager
        self._adapter = adapter
        self._deep_agent_runner = deep_agent_runner
        self._pending_confirm: Dict[str, Dict[str, Any]] = {}

    def run_job(self, job_id: str, todos: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        todos_list = list(todos)
        if not todos_list and self._deep_agent_runner is not None:
            return self._run_deep_agent(job_id, skip_confirm=False)
        return self._run_todos(job_id, todos_list, start_index=0)

    def resume_confirm(self, job_id: str, approved: bool) -> Dict[str, Any]:
        pending = self._pending_confirm.pop(job_id, None)
        if pending is None:
            return {"status": "no_pending"}
        if not approved:
            self._job_manager.update_state(job_id, JobState.CANCELED)
            self._job_manager.append_log(job_id, "confirm rejected")
            return {"status": "canceled"}
        mode = pending.get("mode")
        if mode == "deep_agent":
            return self._run_deep_agent(job_id, skip_confirm=True)
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

    def cancel_job(self, job_id: str) -> None:
        if job_id in self._pending_confirm:
            self._pending_confirm.pop(job_id, None)

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
                    "mode": "todo",
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

    def _run_deep_agent(self, job_id: str, skip_confirm: bool) -> Dict[str, Any]:
        if self._deep_agent_runner is None:
            self._job_manager.set_result(job_id, {"error": "deep_agent_unavailable"}, state=JobState.FAILED)
            return {"status": "failed", "error": "deep_agent_unavailable"}
        job = self._job_manager.get_job(job_id)
        if job is None or not job.request_text:
            self._job_manager.set_result(job_id, {"error": "request_text_missing"}, state=JobState.FAILED)
            return {"status": "failed", "error": "request_text_missing"}
        fast_path = self._maybe_list_directory(job.job_id, job.request_text)
        if fast_path is not None:
            return fast_path
        self._job_manager.update_state(job_id, JobState.RUNNING)
        result = self._deep_agent_runner.run(job.request_text, skip_confirm=skip_confirm)
        if result.status == "waiting_lock":
            self._job_manager.update_state(job_id, JobState.WAITING_LOCK)
            return {"status": "waiting_lock", "reason": result.reason}
        if result.status == "waiting_confirm":
            self._job_manager.update_state(job_id, JobState.WAITING_CONFIRM)
            self._pending_confirm[job_id] = {
                "mode": "deep_agent",
                "request_text": job.request_text,
            }
            return {"status": "waiting_confirm"}
        if result.status == "failed":
            error = result.error or "deep_agent_failed"
            self._job_manager.append_log(job_id, f"deep_agent failed: {error}")
            self._job_manager.update_state(job_id, JobState.FAILED)
            self._job_manager.set_result(job_id, {"error": error}, state=JobState.FAILED)
            return {"status": "failed", "error": error}
        for subagent in extract_subagent_calls(result.output):
            self._job_manager.append_log(job_id, f"subagent_started: {subagent}")
        summary = extract_summary(result.output)
        if summary:
            payload = {"summary": summary, "detail": result.output}
        else:
            payload = {"output": result.output}
        self._job_manager.set_result(job_id, payload, state=JobState.DONE)
        return {"status": "done", "summary": summary}

    def _maybe_list_directory(self, job_id: str, request_text: str) -> Dict[str, Any] | None:
        lower = request_text.lower()
        keywords = [
            "directory",
            "folder",
            "tree",
            "structure",
            "project",
            "\uD3F4\uB354",
            "\uB514\uB809\uD130\uB9AC",
            "\uAD6C\uC870",
            "\uD2B8\uB9AC",
            "\uD504\uB85C\uC81D\uD2B8",
        ]
        if not any(key in lower for key in keywords):
            return None
        self._job_manager.update_state(job_id=job_id, state=JobState.RUNNING)
        result = run_single_todo({"tool": "ListDirTool", "args": {"path": "."}}, self._adapter)
        if result.state == "waiting_lock":
            self._job_manager.update_state(job_id=job_id, state=JobState.WAITING_LOCK)
            return {"status": "waiting_lock", "reason": result.reason}
        if result.state == "waiting_confirm":
            self._job_manager.update_state(job_id=job_id, state=JobState.WAITING_CONFIRM)
            self._pending_confirm[job_id] = {
                "mode": "todo",
                "todo": {"tool": "ListDirTool", "args": {"path": "."}},
                "remaining": [],
            }
            return {"status": "waiting_confirm"}
        if result.state == "failed":
            error = result.error or "listdir_failed"
            self._job_manager.append_log(job_id, f"listdir failed: {error}")
            self._job_manager.update_state(job_id, JobState.FAILED)
            self._job_manager.set_result(job_id, {"error": error}, state=JobState.FAILED)
            return {"status": "failed", "error": error}
        entries = []
        if result.result and isinstance(result.result.get("value"), dict):
            entries = result.result["value"].get("entries", [])
        summary = "Top-level entries: " + ", ".join(entries) if entries else "No entries found."
        self._job_manager.append_log(job_id, "listdir used ListDirTool")
        payload = {"summary": summary, "detail": result.result.get("value") if result.result else None}
        self._job_manager.set_result(job_id, payload, state=JobState.DONE)
        return {"status": "done", "summary": summary}
