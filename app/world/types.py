from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_LOCK = "waiting_lock"
    WAITING_CONFIRM = "waiting_confirm"
    DONE = "done"
    FAILED = "failed"
    CANCELED = "canceled"


class WorkerState(str, Enum):
    RUNNING = "running"
    WAITING_LOCK = "waiting_lock"
    WAITING_CONFIRM = "waiting_confirm"
    DONE = "done"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class ToolCallRecord:
    tool_key: str
    params: Dict[str, Any]
    state: str
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class JobRecord:
    job_id: str
    request_text: Optional[str]
    state: JobState
    logs: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    worker_id: Optional[str] = None
    progress: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
