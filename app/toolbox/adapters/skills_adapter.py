from __future__ import annotations

from typing import Any, Dict

from .base import ToolAdapter


class SkillsAdapter(ToolAdapter):
    def invoke(self, spec: Dict[str, Any], args: Any) -> Any:
        return {
            "ok": False,
            "error": "skills adapter not implemented",
            "tool": spec.get("skills", {}),
            "args": args,
        }
