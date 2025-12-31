from __future__ import annotations

from typing import Any, Dict


class ToolAdapter:
    def invoke(self, spec: Dict[str, Any], args: Any) -> Any:
        raise NotImplementedError
