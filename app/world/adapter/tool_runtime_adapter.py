from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.toolbox.runtime.inventory import Inventory, ToolHandle
from app.toolbox.runtime.router import ToolRuntime


@dataclass
class ToolRuntimeResult:
    state: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    reason: Optional[str] = None


class ToolRuntimeAdapter:
    """Adapter interface for tool execution with inventory/confirm policies."""

    def run(self, todo: Dict[str, Any], skip_confirm: bool = False) -> ToolRuntimeResult:
        raise NotImplementedError

    def acquire(self, tool_key: str, group_key: Optional[str]) -> ToolRuntimeResult:
        raise NotImplementedError

    def confirm_if_needed(self, tool_key: str) -> ToolRuntimeResult:
        raise NotImplementedError

    def execute_tool(self, tool_key: str, params: Dict[str, Any]) -> ToolRuntimeResult:
        raise NotImplementedError

    def release(self, handle: Optional[ToolHandle]) -> ToolRuntimeResult:
        raise NotImplementedError


class InventoryToolRuntimeAdapter(ToolRuntimeAdapter):
    def __init__(self, inventory: Inventory, runtime: ToolRuntime, specs: Dict[str, Dict[str, Any]]) -> None:
        self._inventory = inventory
        self._runtime = runtime
        self._specs = specs

    def run(self, todo: Dict[str, Any], skip_confirm: bool = False) -> ToolRuntimeResult:
        tool_key = todo.get("tool")
        if not tool_key:
            return ToolRuntimeResult(state="done", result=todo.get("result"))
        if not skip_confirm:
            confirm = self.confirm_if_needed(tool_key)
            if confirm.state == "waiting_confirm":
                return confirm
        acquire = self.acquire(tool_key, None)
        if acquire.state != "acquired":
            return acquire
        try:
            result = self.execute_tool(tool_key, todo.get("args", {}))
            return result
        finally:
            self.release(acquire.result.get("handle") if acquire.result else None)

    def acquire(self, tool_key: str, group_key: Optional[str]) -> ToolRuntimeResult:
        # Confirm policy can be checked before acquire to avoid holding a lease.
        acquire = self._inventory.acquire(tool_key)
        if acquire.status != "acquired":
            return ToolRuntimeResult(state="waiting_lock", reason=acquire.reason)
        return ToolRuntimeResult(state="acquired", result={"handle": acquire.handle})

    def confirm_if_needed(self, tool_key: str) -> ToolRuntimeResult:
        spec = self._specs.get(tool_key, {})
        policy = spec.get("confirmPolicy")
        if policy == "always":
            return ToolRuntimeResult(state="waiting_confirm", reason="confirm_required")
        return ToolRuntimeResult(state="approved")

    def execute_tool(self, tool_key: str, params: Dict[str, Any]) -> ToolRuntimeResult:
        try:
            result = self._runtime.invoke(tool_key, params)
            return ToolRuntimeResult(state="done", result={"value": result})
        except Exception as exc:  # pragma: no cover - passthrough error
            return ToolRuntimeResult(state="failed", error=str(exc))

    def release(self, handle: Optional[ToolHandle]) -> ToolRuntimeResult:
        if handle is None:
            return ToolRuntimeResult(state="released")
        self._inventory.release(handle)
        return ToolRuntimeResult(state="released")
