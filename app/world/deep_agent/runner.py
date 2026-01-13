from __future__ import annotations

from dataclasses import dataclass
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


class AdapterTool:
    def __init__(self, tool_key: str, adapter: ToolRuntimeAdapter, description: str, skip_confirm: bool) -> None:
        self.name = tool_key
        self.description = description
        self.__name__ = tool_key
        self.__doc__ = description
        self._adapter = adapter
        self._skip_confirm = skip_confirm

    def __call__(self, **kwargs: Any) -> Any:
        result = self._adapter.run({"tool": self.name, "args": kwargs}, skip_confirm=self._skip_confirm)
        if result.state == "done":
            return result.result.get("value") if result.result else None
        if result.state in ("waiting_lock", "waiting_confirm"):
            raise ToolBlockedError(result.state, result.reason)
        raise RuntimeError(result.error or "tool_failed")


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
        agent = create_deep_agent(llm=llm, tools=tools)
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
            tools.append(AdapterTool(tool_key, self._adapter, description, skip_confirm))
        return tools

    @staticmethod
    def _invoke(agent: Any, request_text: str) -> Any:
        if hasattr(agent, "invoke"):
            return agent.invoke(request_text)
        if hasattr(agent, "run"):
            return agent.run(request_text)
        if callable(agent):
            return agent(request_text)
        raise DeepAgentUnavailable("deep agent runner has no callable interface")
