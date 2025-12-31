from __future__ import annotations

from app.storage.writer import append_log


def log_invoke(tool_key: str, status: str, detail: str = "") -> None:
    message = f"tool={tool_key} status={status}"
    if detail:
        message = f"{message} detail={detail}"
    append_log(message)
