from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class ToolSpec:
    key: str
    spec: Dict[str, Any]


def load_specs(path: str) -> Dict[str, ToolSpec]:
    raise NotImplementedError("Load ToolSpec registry")
