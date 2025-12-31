from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass(frozen=True)
class ToolSpec:
    key: str
    spec: Dict[str, Any]


def load_specs(path: str | Path) -> Dict[str, ToolSpec]:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8-sig") as f:
        data = yaml.safe_load(f) or {}
    tools = data.get("tools", {})
    if not isinstance(tools, dict):
        raise ValueError("ToolSpec registry must include a tools mapping")
    registry: Dict[str, ToolSpec] = {}
    for key, spec in tools.items():
        if not isinstance(spec, dict):
            raise ValueError(f"ToolSpec for {key} must be a mapping")
        registry[key] = ToolSpec(key=key, spec=spec)
    return registry
