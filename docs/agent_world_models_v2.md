# 에이전트 세계관 모델링 (Mermaid)

## 1) 클래스 다이어그램

```mermaid
classDiagram
direction TB

class AgentChatUI {
  +ShowChat(msg)
  +ShowDashboard(status)
  +OpenJobPanel(jobId)
  +StreamLog(jobId, line)
  +EmitUserChoice(jobId, choice)
}

class Customer {
  +SendMessage(text)
}

class GeneralManager {
  +OnUserInput(text)
  +RouteIntent()
  +CreateJob(request)
  +ReplyImmediate()
}

class ProviderAdapter {
  +NormalizePrompt(ctx)
  +ParsePlan(response)
  +ParseToolSpec(response)
  +NormalizeOutput(text)
}

class DeepAgent {
  +Invoke(planOrTodo)
  +RunGraph()
  +CallTool(tool, params)
  +Summarize(result)
}

class JobManager {
  +CreateJob(todos) jobId
  +CancelJob(jobId)
  +GetJobState(jobId)
  +Dispatch()
}

class WorkerPool {
  +Run(n)
  +FetchJob() job
}

class JobRunner {
  +RunJob(job)
  +RunDeepAgent(job)
  +StreamLogs(jobId)
}

class ToolRuntimeAdapter {
  +Acquire(toolKey, groupKey)
  +ConfirmIfNeeded(toolKey)
  +ExecuteTool(toolKey, params)
  +Release(handle)
}

class ToolBox {
  +Acquire(toolKey, groupKey) ToolHandle
  +Release(handle)
  +GetSpecs(toolKey) ToolSpec
}

class ToolSpec {
  +toolKey
  +groupKey
  +capacity
  +confirmPolicy
  +paramsSchema
  +resultSchema
}

class ToolHandle {
  +toolKey
  +groupKey
  +leaseId
}

class Tool {
  +Run(params) result
}

class ToolGroup {
  +groupKey
  +capacity
}

class DashboardBoard {
  +SetWorkerState(workerId, state)
  +Blink(workerId, color)
}

Customer --> AgentChatUI
AgentChatUI --> GeneralManager : user input
GeneralManager --> ProviderAdapter
WorkerPool --> DeepAgent : assign worker
GeneralManager --> JobManager : submit job

JobManager --> WorkerPool
WorkerPool --> JobRunner : assign job
JobRunner --> DeepAgent : run
DeepAgent --> ToolRuntimeAdapter : tool calls
ToolRuntimeAdapter --> ToolBox : acquire, release
ToolBox --> ToolSpec
ToolBox --> ToolGroup
ToolHandle --> Tool
AgentChatUI --> DashboardBoard

note for ToolGroup "MonitorBox\n- shared lock for NavTool, MovieTool\n- capacity=1"
note for ToolSpec "Examples\n- NavTool: groupKey=MonitorBox, capacity=1\n- MovieTool: groupKey=MonitorBox, capacity=1\n- SongTool: groupKey=SongPool, capacity=2\n- WeatherTool: capacity=infinite, no lock"
```

> DeepAgent 내부 그래프는 미들웨어 체인(PatchToolCalls -> Summarization -> model -> TodoList -> tools)로 동작하며, tools 호출은 ToolRuntimeAdapter를 통해 ToolBox를 확인한다.

## 2) 상태 머신(WorkerJob)

```mermaid
stateDiagram-v2

state WorkerJob {
  [*] --> Queued
  Queued --> Running : worker_start
  Running --> WaitingConfirm : confirm_required
  Running --> WaitingLock : tool_locked
  WaitingConfirm --> Running : user_approve
  WaitingConfirm --> Canceled : user_reject
  WaitingLock --> Running : user_wait_or_retry
  WaitingLock --> Canceled : user_cancel
  WaitingLock --> Canceled : user_stop_other
  Running --> Done : job_done
  Running --> Failed : job_failed
  Running --> Canceled : job_canceled
  Done --> [*]
  Failed --> [*]
  Canceled --> [*]
}

note right of WaitingLock
busy means inventory or group lock is held.
default policy: retry SAME TODO (order preserved).
end note

note right of WaitingConfirm
UI shows yellow blink.
click icon opens job panel for approve, cancel, stop.
end note

note right of Running
ToolRuntimeAdapter emits tool_locked/confirm_required.
Worker waits until UI decision is received.
end note
```

> GeneralManager는 LangGraph로 구현하며, DeepAgent는 워커 내부에서 장기 작업을 수행한다.

## 3) GM 라우팅 그래프 (Mermaid)

```mermaid
flowchart TB
  GM_START["WAIT_INPUT"] --> GM_ROUTE{"INTENT_ROUTE"}
  GM_ROUTE -->|start| GM_CREATE["JOB_CREATE"]
  GM_ROUTE -->|status| GM_STATUS["JOB_STATUS_READ"]
  GM_ROUTE -->|cancel| GM_CANCEL["JOB_CANCEL"]
  GM_ROUTE -->|result| GM_RESULT["JOB_RESULT_READ"]
  GM_ROUTE -->|list| GM_LIST["JOB_LIST"]
  GM_CREATE --> GM_REPLY["REPLY_USER"]
  GM_STATUS --> GM_REPLY
  GM_CANCEL --> GM_REPLY
  GM_RESULT --> GM_REPLY
  GM_LIST --> GM_REPLY
  GM_REPLY --> GM_START
```
