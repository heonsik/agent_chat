from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

CONFIG_DIR = Path(__file__).resolve().parent
ROOT_DIR = CONFIG_DIR.parent.parent

_PATH_EXTS = {".yaml", ".yml", ".json", ".md", ".txt"}


def _is_relative_path(value: str) -> bool:
    return not Path(value).is_absolute()


def _resolve_paths(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _resolve_paths(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_paths(v) for v in node]
    if isinstance(node, str):
        suffix = Path(node).suffix.lower()
        if suffix in _PATH_EXTS and _is_relative_path(node):
            return str((ROOT_DIR / node).resolve())
    return node


def load_yaml(path: str | Path) -> Dict[str, Any]:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = CONFIG_DIR / file_path
    with file_path.open("r", encoding="utf-8-sig") as f:
        data = yaml.safe_load(f) or {}
    return _resolve_paths(data)


def load_app_config() -> Dict[str, Any]:
    return load_yaml("app.yaml")


def load_providers_config() -> Dict[str, Any]:
    return load_yaml("providers.yaml")


def load_toolbox_config() -> Dict[str, Any]:
    return load_yaml("toolbox.yaml")


def load_prompts_config() -> Dict[str, Any]:
    return load_yaml("prompts.yaml")


def load_all() -> Dict[str, Any]:
    return {
        "app": load_app_config(),
        "providers": load_providers_config(),
        "toolbox": load_toolbox_config(),
        "prompts": load_prompts_config(),
    }
