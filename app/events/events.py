from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class JobStateEvent:
    job_id: str
    state: str
    detail: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class WorkerStateEvent:
    worker_id: str
    state: str
    detail: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ToolLogEvent:
    job_id: str
    message: str
