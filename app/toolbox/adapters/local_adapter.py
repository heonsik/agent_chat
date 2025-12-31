from __future__ import annotations

from importlib import import_module
from typing import Any, Dict

from .base import ToolAdapter


def _load_entry(entry: str):
    if ":" not in entry:
        raise ValueError(f"Invalid local entry: {entry}")
    module_path, func_name = entry.split(":", 1)
    module = import_module(module_path)
    try:
        return getattr(module, func_name)
    except AttributeError as exc:
        raise ValueError(f"Entry not found: {entry}") from exc


class LocalAdapter(ToolAdapter):
    def invoke(self, spec: Dict[str, Any], args: Any) -> Any:
        local_spec = spec.get("local", {})
        entry = local_spec.get("entry")
        if not entry:
            raise ValueError("Local tool requires local.entry")
        fn = _load_entry(entry)
        if isinstance(args, dict):
            return fn(**args)
        if isinstance(args, (list, tuple)):
            return fn(*args)
        return fn(args)
