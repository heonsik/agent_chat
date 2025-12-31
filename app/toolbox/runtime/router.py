from __future__ import annotations

from typing import Any, Dict

from .logs import log_invoke
from .registry import ToolSpec


class ToolRuntime:
    def __init__(self, specs: Dict[str, ToolSpec], adapters: Dict[str, Any]):
        self._specs = specs
        self._adapters = adapters

    def invoke(self, tool_key: str, args: Any) -> Any:
        spec_entry = self._specs.get(tool_key)
        if spec_entry is None:
            raise KeyError(f"Unknown tool: {tool_key}")
        spec = spec_entry.spec
        tool_type = spec.get("type", "local")
        adapter = self._adapters.get(tool_type)
        if adapter is None:
            raise ValueError(f"No adapter for tool type: {tool_type}")
        result = adapter.invoke(spec, args)
        log_invoke(tool_key, "ok")
        return result
