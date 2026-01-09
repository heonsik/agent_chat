# 에이전트 세계관 플로우차트 (Mermaid 전용, v3)

아래 Mermaid 코드를 Mermaid Live Editor에 붙여넣어 확인하세요.

```mermaid
flowchart TB

%% =========================
%% STYLE DEFINITIONS
%% =========================
classDef ui fill:#F1F8E9,stroke:#7CB342,stroke-width:2px,color:#1B5E20;
classDef main fill:#E3F2FD,stroke:#1E88E5,stroke-width:2px,color:#0D47A1;
classDef worker fill:#E8F5E9,stroke:#43A047,stroke-width:2px,color:#1B5E20;
classDef tool fill:#ECEFF1,stroke:#546E7A,stroke-width:2px,color:#263238;

classDef decision fill:#F3E5F5,stroke:#8E24AA,stroke-width:2px,color:#4A148C;
classDef warn fill:#FFF3E0,stroke:#FB8C00,stroke-width:2px,color:#E65100;
classDef danger fill:#FFEBEE,stroke:#E53935,stroke-width:2px,color:#B71C1C;

%% LLM CALL (distinct)
classDef llm fill:#0D47A1,stroke:#00E5FF,stroke-width:4px,color:#FFFFFF;

%% =========================
%% UI (가게/전광판/작업패널)
%% =========================
subgraph UI["PROGRAM UI (agent_chat) - 가게"]
  U_CHAT["CHAT_VIEW<br/>고객 채팅"]:::ui
  U_BOARD["DASHBOARD<br/>전광판: 워커/잡 상태"]:::ui
  U_PANEL["JOB_PANEL<br/>작업별 채팅/로그/승인"]:::ui
  U_LOG["LOG_STREAM<br/>툴 로그 표시"]:::ui
  U_BTN["CONFIRM_BUTTONS<br/>상태별 옵션 표시"]:::ui

  U_CHAT --> U_PANEL
  U_BOARD --> U_PANEL
  U_PANEL --> U_LOG
  U_PANEL --> U_BTN
end

CUST["CUSTOMER<br/>고객(사용자)"] --> U_CHAT

%% =========================
%% GENERAL MANAGER (LangGraph)
%% =========================
subgraph MAIN["GENERAL_MANAGER - 총괄매니저(LangGraph)"]
  M_WAIT["WAIT_INPUT<br/>입력대기"]:::main
  M_ROUTE["INTENT_ROUTE<br/>START/STATUS/CANCEL/RESULT/LIST"]:::main
  M_CREATE["JOB_CREATE<br/>작업지시서 생성"]:::main
  M_STATUS["JOB_STATUS_READ<br/>상태 조회"]:::main
  M_CANCEL["JOB_CANCEL<br/>취소 요청"]:::danger
  M_RESULT["JOB_RESULT_READ<br/>결과 요약 요청"]:::main
  M_REPLY["REPLY_USER<br/>즉시 응답"]:::main

  M_WAIT --> M_ROUTE
  M_ROUTE -->|start| M_CREATE --> M_REPLY --> U_CHAT --> M_WAIT
  M_ROUTE -->|status| M_STATUS --> M_REPLY --> U_CHAT --> M_WAIT
  M_ROUTE -->|cancel| M_CANCEL --> M_REPLY --> U_CHAT --> M_WAIT
  M_ROUTE -->|result| M_RESULT --> M_REPLY --> U_CHAT --> M_WAIT
  M_ROUTE -->|list| M_REPLY --> U_CHAT --> M_WAIT
end

U_CHAT --> M_WAIT

%% =========================
%% JOB MANAGER (작업표/배차/취소)
%% =========================
subgraph JM["JOB_MANAGER - 작업표, 배차, 취소"]
  JM_IN["SUBMIT_IN<br/>작업지시서 수신"]:::main --> JM_CREATE["CREATE_JOB<br/>job_id 생성"]:::main
  JM_CREATE --> JM_QUEUE["JOB_QUEUE<br/>대기열"]:::main
  JM_CANCEL["CANCEL_JOB<br/>현재 Job 취소"]:::danger
  JM_CANCEL_CONFLICT["CANCEL_CONFLICT_JOB<br/>충돌 Job 취소"]:::danger
end

M_SUBMIT --> JM_IN

%% =========================
%% SERVERS (워커 풀)
%% =========================
subgraph WP["SERVERS - 서버들(WorkerPool, N개 동시 실행)"]
  W_FETCH["FETCH_JOB<br/>작업 가져오기"]:::worker
  W_RUN["JOB_RUNNER<br/>DeepAgent 실행 어댑터"]:::worker
  W_DONE["JOB_DONE<br/>완료"]:::worker
  W_FAIL["JOB_FAIL<br/>실패"]:::danger
  W_CANC["JOB_CANCELED<br/>취소"]:::warn

  W_FETCH --> W_RUN
  W_RUN -->|success| W_DONE
  W_RUN -->|fail| W_FAIL
  W_RUN -->|canceled| W_CANC
end

JM_QUEUE --> W_FETCH

%% =========================
%% TOOLBOX (공구박스: 수량, 그룹락)
%% =========================
subgraph TBX["TOOLBOX - 공구박스(재고, 수량, 그룹락)"]
  T_SPEC["TOOL_SPECS<br/>설명서: params, result, capacity, groupKey"]:::tool
  T_INV["INVENTORY<br/>대여현황"]:::tool
  T_ACQ["ACQUIRE<br/>대여 요청"]:::tool
  T_REL["RELEASE<br/>반납"]:::tool

  T_MON["GROUP: MonitorBox<br/>NavTool(1), MovieTool(1)<br/>공유락: capacity=1"]:::tool
  T_SONG["POOL: SONG_TOOL<br/>SongTool(2)"]:::tool
  T_WEAT["POOL: WEATHER_TOOL<br/>WeatherTool(infinite)<br/>락 없음"]:::tool
end

%% =========================
%% DEEP AGENT (Worker 내부)
%% =========================
subgraph DA["DEEP_AGENT - 워커 내부 실행"]
  D_PLAN["PLAN/TODO<br/>작업 분해"]:::llm
  D_STEP["STEP_LOOP<br/>todo 순차 처리"]:::worker
  D_NEED{"NEED_TOOL?<br/>툴 필요"}:::decision
  D_SOLVE["LLM_SOLVER<br/>툴 없이 해결"]:::llm
  D_TOOL["CALL_TOOL<br/>툴 호출"]:::tool
  D_EVI{"NEED_EVIDENCE?<br/>근거 필요"}:::decision
  D_REPORT["LLM_EVIDENCE<br/>결과 요약"]:::llm

  D_PLAN --> D_STEP --> D_NEED
  D_NEED -->|no| D_SOLVE --> D_STEP
  D_NEED -->|yes| D_TOOL --> D_EVI
  D_EVI -->|yes| D_REPORT --> D_STEP
  D_EVI -->|no| D_STEP
end

%% =========================
%% TOOL RUNTIME ADAPTER (정책 강제)
%% =========================
subgraph TRA["TOOL_RUNTIME_ADAPTER - 정책 강제"]
  A_ACQ["ACQUIRE<br/>대여 요청"]:::tool
  A_AVAIL{"AVAILABLE?<br/>재고/그룹락"}:::decision
  A_WAIT_LOCK["INTERRUPT<br/>대기/취소/중단"]:::warn
  A_CONFIRM{"CONFIRM_REQUIRED?<br/>승인 필요"}:::decision
  A_WAIT_CONFIRM["INTERRUPT<br/>승인/거부"]:::warn
  A_EXEC["RUN_TOOL<br/>툴 실행"]:::tool
  A_REL["RELEASE<br/>반납"]:::tool

  A_ACQ --> A_AVAIL
  A_AVAIL -->|yes| A_CONFIRM
  A_AVAIL -->|no| A_WAIT_LOCK
  A_CONFIRM -->|no| A_EXEC --> A_REL
  A_CONFIRM -->|yes| A_WAIT_CONFIRM
end

W_RUN --> D_PLAN
D_TOOL --> A_ACQ

%% Toolbox wiring
A_ACQ --> T_ACQ --> T_INV
T_INV -->|acquired| A_AVAIL
T_INV -->|locked| A_AVAIL
A_REL --> T_REL --> T_INV
A_ACQ -.->|via toolbox| A_AVAIL

%% User choice wiring (UI)
A_WAIT_LOCK -->|ui_state: waiting_lock| U_BOARD
A_WAIT_CONFIRM -->|ui_state: waiting_confirm| U_BOARD
A_WAIT_LOCK --> U_PANEL
A_WAIT_CONFIRM --> U_PANEL
A_WAIT_LOCK -->|options: wait/cancel/stop_other| U_BTN
A_WAIT_CONFIRM -->|options: approve/reject| U_BTN

U_BTN -->|choice_wait: auto_retry| A_ACQ
U_BTN -->|choice_cancel: cancel_current_job| JM_CANCEL
U_BTN -->|choice_stop_other: cancel_conflict_job| JM_CANCEL_CONFLICT
U_BTN -->|choice_approve: run_tool| A_EXEC
U_BTN -->|choice_reject: cancel_current_job| JM_CANCEL

%% UI status updates
W_RUN -.->|event: running| U_BOARD
W_DONE -.->|event: done_green_blink| U_BOARD
W_FAIL -.->|event: fail_red_blink| U_BOARD
W_CANC -.->|event: canceled_gray| U_BOARD
A_EXEC -.->|log_stream| U_LOG
```

> 참고: GeneralManager는 LangGraph로 구현한다. DeepAgent는 워커 내부 실행기이며, ToolRuntimeAdapter가 ToolBox 정책을 강제한다.
