from __future__ import annotations

from typing import Any, Dict

from app.toolbox.runtime.inventory import Inventory
from app.toolbox.runtime.router import ToolRuntime


def run_single_todo(
    todo: Dict[str, Any],
    inventory: Inventory,
    runtime: ToolRuntime,
) -> Dict[str, Any]:
    tool_key = todo.get("tool")
    if not tool_key:
        return {"status": "done", "result": todo.get("result")}

    acquire = inventory.acquire(tool_key)
    if acquire.status != "acquired":
        return {"status": "locked", "reason": acquire.reason}

    try:
        result = runtime.invoke(tool_key, todo.get("args", {}))
        return {"status": "done", "result": result}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    finally:
        if acquire.handle:
            inventory.release(acquire.handle)
