from __future__ import annotations

from typing import Any, Dict

from .base import ToolAdapter


class McpAdapter(ToolAdapter):
    def invoke(self, spec: Dict[str, Any], args: Any) -> Any:
        return {
            "ok": False,
            "error": "mcp adapter not implemented",
            "tool": spec.get("mcp", {}),
            "args": args,
        }
