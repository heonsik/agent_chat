from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import uuid4


def _parse_capacity(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, str) and value.lower() == "infinite":
        return None
    if isinstance(value, int) and value >= 0:
        return value
    raise ValueError(f"Invalid capacity: {value}")


def _min_capacity(a: Optional[int], b: Optional[int]) -> Optional[int]:
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)


@dataclass(frozen=True)
class ToolHandle:
    tool_key: str
    group_key: Optional[str]
    lease_id: str


@dataclass(frozen=True)
class AcquireResult:
    status: str  # acquired | locked
    handle: Optional[ToolHandle]
    reason: Optional[str]


class Inventory:
    def __init__(self, specs: Dict[str, Dict[str, Any]]):
        self._specs = specs
        self._tool_caps: Dict[str, Optional[int]] = {}
        self._group_caps: Dict[str, Optional[int]] = {}
        self._tool_use: Dict[str, int] = {}
        self._group_use: Dict[str, int] = {}
        self._leases: Dict[str, ToolHandle] = {}
        self._init_caps()

    def _init_caps(self) -> None:
        for key, spec in self._specs.items():
            cap = _parse_capacity(spec.get("capacity"))
            self._tool_caps[key] = cap
            self._tool_use.setdefault(key, 0)
            group_key = spec.get("groupKey")
            if group_key:
                group_cap_raw = spec.get("groupCapacity", spec.get("capacity"))
                group_cap = _parse_capacity(group_cap_raw)
                if group_key not in self._group_caps:
                    self._group_caps[group_key] = group_cap
                else:
                    self._group_caps[group_key] = _min_capacity(
                        self._group_caps[group_key], group_cap
                    )
                self._group_use.setdefault(group_key, 0)

    def acquire(self, tool_key: str) -> AcquireResult:
        if tool_key not in self._specs:
            raise KeyError(f"Unknown tool: {tool_key}")
        spec = self._specs[tool_key]
        group_key = spec.get("groupKey")
        if not self._has_capacity(tool_key, group_key):
            return AcquireResult(status="locked", handle=None, reason="capacity")
        lease_id = uuid4().hex
        handle = ToolHandle(tool_key=tool_key, group_key=group_key, lease_id=lease_id)
        self._leases[lease_id] = handle
        self._tool_use[tool_key] += 1
        if group_key:
            self._group_use[group_key] += 1
        return AcquireResult(status="acquired", handle=handle, reason=None)

    def release(self, handle: ToolHandle) -> None:
        if handle is None:
            return
        lease = self._leases.pop(handle.lease_id, None)
        if lease is None:
            return
        self._tool_use[lease.tool_key] = max(0, self._tool_use[lease.tool_key] - 1)
        if lease.group_key:
            self._group_use[lease.group_key] = max(
                0, self._group_use[lease.group_key] - 1
            )

    def _has_capacity(self, tool_key: str, group_key: Optional[str]) -> bool:
        tool_cap = self._tool_caps.get(tool_key)
        if tool_cap is not None and self._tool_use[tool_key] >= tool_cap:
            return False
        if group_key:
            group_cap = self._group_caps.get(group_key)
            if group_cap is not None and self._group_use[group_key] >= group_cap:
                return False
        return True
