from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.world.events import EventBus
from app.world.types import JobRecord, JobState


class JobManager:
    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._event_bus = event_bus

    def create_job(self, request_text: Optional[str], metadata: Optional[Dict[str, Any]] = None) -> JobRecord:
        job_id = uuid4().hex
        job = JobRecord(
            job_id=job_id,
            request_text=request_text,
            state=JobState.QUEUED,
            metadata=metadata or {},
        )
        self._jobs[job_id] = job
        self._publish("job_created", job)
        return job

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        return self._jobs.get(job_id)

    def list_jobs(self) -> List[JobRecord]:
        return list(self._jobs.values())

    def cancel_job(self, job_id: str, reason: Optional[str] = None) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.state = JobState.CANCELED
        job.updated_at = datetime.utcnow()
        if reason:
            job.logs.append(f"canceled: {reason}")
        self._publish("job_canceled", job)
        return True

    def update_state(self, job_id: str, state: JobState) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.state = state
        job.updated_at = datetime.utcnow()
        self._publish("job_state", job)
        return True

    def append_log(self, job_id: str, line: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.logs.append(line)
        job.updated_at = datetime.utcnow()
        self._publish("job_log", job)
        return True

    def set_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.result = result
        job.state = JobState.DONE
        job.updated_at = datetime.utcnow()
        self._publish("job_done", job)
        return True

    def _publish(self, event_type: str, job: JobRecord) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            event_type,
            {
                "job_id": job.job_id,
                "state": job.state.value,
                "logs": job.logs,
                "result": job.result,
                "updated_at": job.updated_at.isoformat(),
            },
        )
