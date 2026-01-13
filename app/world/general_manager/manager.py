from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from app.world.wiring import WorldWiring


@dataclass
class GMResponse:
    text: str
    job_id: Optional[str] = None


class GeneralManager:
    def __init__(self, wiring: WorldWiring, llm: Any | None = None) -> None:
        self._wiring = wiring
        self._llm = llm
        self._graph = self._build_graph()

    def handle(self, text: str, todos: Optional[list[dict[str, Any]]] = None) -> GMResponse:
        state = self._graph.invoke({"text": text, "todos": todos})
        return GMResponse(text=state.get("response_text", "unknown command"), job_id=state.get("job_id"))

    def _route_intent(self, text: str) -> str:
        lower = text.strip().lower()
        if lower.startswith("start"):
            return "start"
        if lower.startswith("status"):
            return "status"
        if lower.startswith("cancel"):
            return "cancel"
        if lower.startswith("result"):
            return "result"
        if lower.startswith("list"):
            return "list"
        if lower.startswith("help"):
            return "help"
        return "unknown"

    def _route_intent_llm(self, text: str) -> str:
        if self._llm is None:
            return self._route_intent(text)
        prompt = (
            "Classify the user request into one of: start, status, cancel, result, list, help, unknown.\n"
            f"Request: {text}\n"
            "Return only the label."
        )
        try:
            response = self._llm.invoke(prompt)
            content = getattr(response, "content", "") if response else ""
            intent = (content or "").strip().lower()
            return intent if intent in {"start", "status", "cancel", "result", "list", "help"} else "unknown"
        except Exception:
            return self._route_intent(text)

    def _extract_job_id(self, text: str) -> Optional[str]:
        parts = text.split()
        if len(parts) >= 2:
            return parts[1]
        return None

    def _build_graph(self):
        graph = StateGraph(dict)

        def route_intent(state: Dict[str, Any]) -> Dict[str, Any]:
            text = state.get("text", "")
            intent = self._route_intent_llm(text)
            return {"intent": intent}

        def handle_start(state: Dict[str, Any]) -> Dict[str, Any]:
            todos = state.get("todos")
            text = state.get("text", "")
            if todos is None and not self._wiring.supports_deep_agent():
                return {"response_text": "todo required"}
            job_id = self._wiring.submit_job(text, todos)
            return {"response_text": f"accepted job_id={job_id}", "job_id": job_id}

        def handle_status(state: Dict[str, Any]) -> Dict[str, Any]:
            text = state.get("text", "")
            job_id = self._extract_job_id(text)
            if not job_id:
                return {"response_text": "job_id required"}
            job = self._wiring.job_manager.get_job(job_id)
            if job is None:
                return {"response_text": "not found"}
            return {"response_text": f"state={job.state.value}", "job_id": job_id}

        def handle_cancel(state: Dict[str, Any]) -> Dict[str, Any]:
            text = state.get("text", "")
            job_id = self._extract_job_id(text)
            if not job_id:
                return {"response_text": "job_id required"}
            canceled = self._wiring.cancel_job(job_id)
            return {"response_text": "canceled" if canceled else "not found", "job_id": job_id}

        def handle_result(state: Dict[str, Any]) -> Dict[str, Any]:
            text = state.get("text", "")
            job_id = self._extract_job_id(text)
            if not job_id:
                return {"response_text": "job_id required"}
            job = self._wiring.job_manager.get_job(job_id)
            if job is None:
                return {"response_text": "not found"}
            return {"response_text": f"result={job.result}", "job_id": job_id}

        def handle_list(state: Dict[str, Any]) -> Dict[str, Any]:
            jobs = self._wiring.job_manager.list_jobs()
            summary = ", ".join([f"{job.job_id}:{job.state.value}" for job in jobs]) or "empty"
            return {"response_text": f"jobs={summary}"}

        def handle_help(state: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "response_text": (
                    "commands: start <ToolKey> [k=v], status <job_id>, "
                    "result <job_id>, cancel <job_id>, list"
                )
            }

        def handle_unknown(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"response_text": "unknown command"}

        graph.add_node("route_intent", route_intent)
        graph.add_node("handle_start", handle_start)
        graph.add_node("handle_status", handle_status)
        graph.add_node("handle_cancel", handle_cancel)
        graph.add_node("handle_result", handle_result)
        graph.add_node("handle_list", handle_list)
        graph.add_node("handle_help", handle_help)
        graph.add_node("handle_unknown", handle_unknown)

        graph.set_entry_point("route_intent")
        graph.add_conditional_edges(
            "route_intent",
            lambda state: state.get("intent"),
            {
                "start": "handle_start",
                "status": "handle_status",
                "cancel": "handle_cancel",
                "result": "handle_result",
                "list": "handle_list",
                "help": "handle_help",
                "unknown": "handle_unknown",
            },
        )
        graph.add_edge("handle_start", END)
        graph.add_edge("handle_status", END)
        graph.add_edge("handle_cancel", END)
        graph.add_edge("handle_result", END)
        graph.add_edge("handle_list", END)
        graph.add_edge("handle_help", END)
        graph.add_edge("handle_unknown", END)

        return graph.compile()
