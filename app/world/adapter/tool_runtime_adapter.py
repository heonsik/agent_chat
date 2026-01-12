from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ToolRuntimeResult:
    state: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ToolRuntimeAdapter:
    """Adapter interface for tool execution with inventory/confirm policies."""

    def acquire(self, tool_key: str, group_key: Optional[str]) -> ToolRuntimeResult:
        raise NotImplementedError

    def confirm_if_needed(self, tool_key: str) -> ToolRuntimeResult:
        raise NotImplementedError

    def execute_tool(self, tool_key: str, params: Dict[str, Any]) -> ToolRuntimeResult:
        raise NotImplementedError

    def release(self, tool_key: str, group_key: Optional[str]) -> ToolRuntimeResult:
        raise NotImplementedError
