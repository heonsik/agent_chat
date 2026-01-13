from __future__ import annotations

from dataclasses import dataclass
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from app.world.adapter.tool_runtime_adapter import ToolRuntimeAdapter


class DeepAgentUnavailable(RuntimeError):
    pass


class ToolBlockedError(RuntimeError):
    def __init__(self, state: str, reason: Optional[str] = None) -> None:
        super().__init__(state)
        self.state = state
        self.reason = reason


@dataclass
class DeepAgentResult:
    status: str
    output: Optional[Any] = None
    error: Optional[str] = None
    reason: Optional[str] = None


def _build_tool(
    tool_key: str,
    adapter: ToolRuntimeAdapter,
    description: str,
    skip_confirm: bool,
    input_schema: Optional[Dict[str, Any]] = None,
) -> Callable[..., Any]:
    def tool(**kwargs: Any) -> Any:
        result = adapter.run({"tool": tool_key, "args": kwargs}, skip_confirm=skip_confirm)
        if result.state == "done":
            return result.result.get("value") if result.result else None
        if result.state in ("waiting_lock", "waiting_confirm"):
            raise ToolBlockedError(result.state, result.reason)
        raise RuntimeError(result.error or "tool_failed")

    tool.__name__ = tool_key
    tool.__doc__ = description
    if input_schema:
        _apply_signature(tool, input_schema)
    return tool


def _apply_signature(tool: Callable[..., Any], schema: Dict[str, Any]) -> None:
    properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
    required = set(schema.get("required", []) if isinstance(schema, dict) else [])
    params: list[inspect.Parameter] = []
    annotations: Dict[str, Any] = {}
    for name in properties.keys():
        default = inspect.Parameter.empty if name in required else None
        params.append(
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                default=default,
                annotation=Any,
            )
        )
        annotations[name] = Any
    if params:
        tool.__signature__ = inspect.Signature(parameters=params)
        annotations["return"] = Any
        tool.__annotations__ = annotations


class DeepAgentRunner:
    def __init__(
        self,
        adapter: ToolRuntimeAdapter,
        specs: Dict[str, Dict[str, Any]],
        llm_factory: Optional[Callable[[], Any]] = None,
    ) -> None:
        self._adapter = adapter
        self._specs = specs
        self._llm_factory = llm_factory
        self._agent: Optional[Any] = None

    def run(self, request_text: str, skip_confirm: bool = False) -> DeepAgentResult:
        agent = self._get_agent(skip_confirm=skip_confirm)
        try:
            output = self._invoke(agent, request_text)
            return DeepAgentResult(status="done", output=output)
        except ToolBlockedError as exc:
            return DeepAgentResult(status=exc.state, reason=exc.reason)
        except Exception as exc:
            return DeepAgentResult(status="failed", error=str(exc))

    def _get_agent(self, skip_confirm: bool) -> Any:
        if self._agent is not None and not skip_confirm:
            return self._agent
        create_deep_agent = self._load_create_deep_agent()
        llm = self._create_llm()
        tools = self._build_tools(skip_confirm=skip_confirm)
        system_prompt = self._load_prompt("system.md")
        agent = create_deep_agent(model=llm, tools=tools, system_prompt=system_prompt)
        if not skip_confirm:
            self._agent = agent
        return agent

    def _load_create_deep_agent(self) -> Callable[..., Any]:
        try:
            from deepagents import create_deep_agent  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise DeepAgentUnavailable("deepagents is not installed") from exc
        return create_deep_agent

    def _create_llm(self) -> Any:
        if self._llm_factory is None:
            raise DeepAgentUnavailable("llm_factory is not configured")
        return self._llm_factory()

    def _build_tools(self, skip_confirm: bool) -> list[Any]:
        tools: list[Any] = []
        for tool_key, spec in self._specs.items():
            description = spec.get("description") or ""
            input_schema = spec.get("inputSchema") or {}
            tools.append(_build_tool(tool_key, self._adapter, description, skip_confirm, input_schema))
        return tools

    def _load_prompt(self, filename: str) -> str:
        path = Path(__file__).resolve().parent / "prompts" / filename
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _invoke(agent: Any, request_text: str) -> Any:
        if hasattr(agent, "invoke"):
            try:
                return agent.invoke(request_text)
            except Exception:
                return agent.invoke({"messages": [("user", request_text)]})
        if hasattr(agent, "run"):
            return agent.run(request_text)
        if callable(agent):
            return agent(request_text)
        raise DeepAgentUnavailable("deep agent runner has no callable interface")


def extract_summary(output: Any) -> Optional[str]:
    if isinstance(output, str):
        return output
    if isinstance(output, dict):
        messages = output.get("messages")
        if isinstance(messages, list):
            for msg in reversed(messages):
                if isinstance(msg, dict):
                    content = msg.get("content")
                else:
                    content = getattr(msg, "content", None)
                if isinstance(content, str) and content.strip():
                    return content
    return None


def extract_subagent_calls(output: Any) -> list[str]:
    messages = []
    if isinstance(output, dict):
        messages = output.get("messages", [])
    elif isinstance(output, list):
        messages = output
    subagents: list[str] = []
    for msg in messages:
        tool_calls = []
        if isinstance(msg, dict):
            tool_calls = msg.get("tool_calls", []) or []
        else:
            tool_calls = getattr(msg, "tool_calls", []) or []
        for call in tool_calls:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name != "task":
                continue
            args = call.get("args") if isinstance(call, dict) else getattr(call, "args", None)
            subagent_type = None
            if isinstance(args, dict):
                subagent_type = args.get("subagent_type")
            if subagent_type:
                subagents.append(str(subagent_type))
            else:
                subagents.append("task")
    return subagents
