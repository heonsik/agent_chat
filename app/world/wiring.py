from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from typing import Any, Dict

from app.toolbox.adapters import LocalAdapter, McpAdapter, SkillsAdapter
from app.toolbox.runtime.inventory import Inventory
from app.toolbox.runtime.registry import load_specs
from app.toolbox.runtime.router import ToolRuntime
from app.world.adapter.tool_runtime_adapter import InventoryToolRuntimeAdapter
from app.world.events import EventBus
from app.world.job_manager import JobManager
from app.world.job_runner import JobRunner
from app.world.worker_pool import WorkerPool


class WorldWiring:
    def __init__(self, specs_path: str | Path, adapters: Dict[str, Any] | None = None) -> None:
        self._specs_path = Path(specs_path)
        self._adapters = adapters or {
            "local": LocalAdapter(),
            "mcp": McpAdapter(),
            "skills": SkillsAdapter(),
        }
        self.event_bus = EventBus()
        self._stop_event = Event()
        self._worker_thread: Thread | None = None

        registry = load_specs(self._specs_path)
        specs_dict = {key: spec.spec for key, spec in registry.items()}
        self.inventory = Inventory(specs_dict)
        self.runtime = ToolRuntime(registry, self._adapters)
        self.tool_adapter = InventoryToolRuntimeAdapter(self.inventory, self.runtime, specs_dict)

        self.job_manager = JobManager(event_bus=self.event_bus)
        self.job_runner = JobRunner(self.job_manager, self.tool_adapter)
        self.worker_pool = WorkerPool(self.job_runner)
        self.job_manager.set_worker_pool(self.worker_pool)

    def start_workers(self) -> None:
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        self._worker_thread = Thread(
            target=self.worker_pool.run_loop,
            args=(self._stop_event.is_set,),
            daemon=True,
        )
        self._worker_thread.start()

    def stop_workers(self) -> None:
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=1.0)

    def submit_job(self, request_text: str, todos: list[dict[str, Any]]) -> str:
        job = self.job_manager.create_job(request_text)
        self.job_manager.dispatch(job.job_id, todos)
        return job.job_id

    def approve_job(self, job_id: str) -> None:
        self.job_runner.resume_confirm(job_id, approved=True)

    def reject_job(self, job_id: str) -> None:
        self.job_runner.resume_confirm(job_id, approved=False)
