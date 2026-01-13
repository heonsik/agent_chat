from __future__ import annotations

from typing import Any, Dict
import json
import os
import re
import urllib.request

from .base import ToolAdapter


class McpAdapter(ToolAdapter):
    def invoke(self, spec: Dict[str, Any], args: Any) -> Any:
        mcp_spec = spec.get("mcp", {})
        server = mcp_spec.get("server")
        tool_name = mcp_spec.get("tool_name")
        if not server or not tool_name:
            return {
                "ok": False,
                "error": "mcp spec missing server or tool_name",
                "tool": mcp_spec,
                "args": args,
            }
        env_key = _server_env_key(server)
        server_url = os.environ.get(env_key)
        if not server_url:
            return {
                "ok": False,
                "error": f"missing env var {env_key} for mcp server url",
                "tool": mcp_spec,
                "args": args,
            }
        payload = {"tool": tool_name, "args": args}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            server_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc),
                "tool": mcp_spec,
                "args": args,
            }
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {"ok": True, "result": raw.decode("utf-8", errors="replace")}


def _server_env_key(server: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", server).upper()
    return f"MCP_SERVER_{normalized}_URL"
