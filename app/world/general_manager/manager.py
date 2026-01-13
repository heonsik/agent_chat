from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.world.wiring import WorldWiring


@dataclass
class GMResponse:
    text: str
    job_id: Optional[str] = None


class GeneralManager:
    def __init__(self, wiring: WorldWiring) -> None:
        self._wiring = wiring

    def handle(self, text: str, todos: Optional[list[dict[str, Any]]] = None) -> GMResponse:
        intent = self._route_intent(text)
        if intent == "start":
            if todos is None:
                return GMResponse(text="todo required", job_id=None)
            job_id = self._wiring.submit_job(text, todos)
            return GMResponse(text=f"accepted job_id={job_id}", job_id=job_id)
        if intent == "status":
            job_id = self._extract_job_id(text)
            if not job_id:
                return GMResponse(text="job_id required", job_id=None)
            job = self._wiring.job_manager.get_job(job_id)
            if job is None:
                return GMResponse(text="not found", job_id=None)
            return GMResponse(text=f"state={job.state.value}", job_id=job_id)
        if intent == "cancel":
            job_id = self._extract_job_id(text)
            if not job_id:
                return GMResponse(text="job_id required", job_id=None)
            canceled = self._wiring.cancel_job(job_id)
            return GMResponse(text="canceled" if canceled else "not found", job_id=job_id)
        if intent == "result":
            job_id = self._extract_job_id(text)
            if not job_id:
                return GMResponse(text="job_id required", job_id=None)
            job = self._wiring.job_manager.get_job(job_id)
            if job is None:
                return GMResponse(text="not found", job_id=None)
            return GMResponse(text=f"result={job.result}", job_id=job_id)
        if intent == "list":
            jobs = self._wiring.job_manager.list_jobs()
            summary = ", ".join([f"{job.job_id}:{job.state.value}" for job in jobs]) or "empty"
            return GMResponse(text=f"jobs={summary}")
        if intent == "help":
            return GMResponse(text="commands: start <ToolKey> [k=v], status <job_id>, result <job_id>, cancel <job_id>, list")
        return GMResponse(text="unknown command")

    def _route_intent(self, text: str) -> str:
        lower = text.strip().lower()
        if lower.startswith("start"):
            return "start"
        if lower.startswith("status"):
            return "status"
        if lower.startswith("cancel"):
            return "cancel"
        if lower.startswith("result"):
            return "result"
        if lower.startswith("list"):
            return "list"
        if lower.startswith("help"):
            return "help"
        return "unknown"

    def _extract_job_id(self, text: str) -> Optional[str]:
        parts = text.split()
        if len(parts) >= 2:
            return parts[1]
        return None
