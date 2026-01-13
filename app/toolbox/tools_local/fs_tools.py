from __future__ import annotations

from pathlib import Path
from typing import Dict, List


def list_directory(path: str = ".") -> Dict[str, List[str]]:
    base = Path(path).resolve()
    entries = sorted([p.name for p in base.iterdir()])
    return {"path": str(base), "entries": entries}
