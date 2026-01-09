# 에이전트 프로그램 설명서 (세계관 기반)

이 문서는 ‘가게 세계관’(통역가/총괄매니저/서버/공구박스/전광판) 기반으로 프로그램이 어떻게 동작해야 하는지 **구현 관점**에서 설명합니다.

---

## 1) 용어 매핑 (세계관 -> 코드)

- **고객(Customer)**: 사용자 입력/출력의 주체
- **프로그램(agent_chat / UI)**: Chat View + 전광판(Dashboard) + Job Panel
- **총괄매니저(GeneralManager / LangGraph)**: 입력을 분기하고 Job을 생성/조회/취소하는 최상위 오케스트레이터
- **딥에이전트(DeepAgent / Worker)**: Job을 받아 장시간 작업을 수행하고 툴 호출/판단/요약을 책임지는 워커
- **프로바이더(ProviderAdapter)**: LLM별 I/O 포맷을 통일하는 어댑터(필요 시 GM/Worker 모두 사용)
- **서버들(WorkerPool + JobRunner)**: Job을 받아 DeepAgent로 실행시키는 런처/풀
- **공구박스(ToolBox)**: 툴 인벤토리(수량, 그룹락, 대여/반납)
- **툴런타임 어댑터(ToolRuntimeAdapter)**: DeepAgent의 툴 호출을 ToolBox 정책(Acquire/Release/승인)으로 감싸는 실행 계층
- **전광판(Dashboard)**: 워커/잡 상태를 상시 표시하는 UI 컴포넌트(색/깜빡임)
- **전광판 상태관리자(DashboardBoard)**: 전광판(UI)의 상태를 이벤트로 갱신하는 백엔드 컴포넌트

---

## 2) 실행 개요 (Top-level)

1. 고객이 채팅으로 요청한다.
2. 총괄매니저(LangGraph)는 입력을 분기한다. (새 작업 / 상태조회 / 취소 / 결과요약)
3. 새 작업이면 JobManager에 작업지시서를 제출하고 **즉시 응답**한다.
4. JobRunner는 WorkerPool에서 DeepAgent를 할당하고 작업을 시작한다.
5. DeepAgent는 계획/툴선택/파라미터/실행/요약을 **백그라운드에서 수행**한다.
6. DeepAgent의 툴 호출은 ToolRuntimeAdapter를 통해 ToolBox 정책(Acquire/Release, 승인, 그룹락)을 강제한다.
7. 승인/충돌/락 대기는 Job Panel에서 처리되며, DeepAgent는 해당 결정이 내려질 때까지 대기한다.

---

## 3) LLM 호출 지점 (성능 최우선)

권장 호출 포인트는 **GM 경량 분기 + Worker(DeepAgent) 장기 실행**으로 분리한다.

### 3.1) GM(LangGraph) 측
- **Intent Router**: 입력을 분기(START/STATUS/CANCEL/RESULT/LIST)
- **Reply Generator(선택)**: 상태/에러/요약 응답을 간단히 작성

### 3.2) Worker(DeepAgent) 측
- **Planner**: 요청 해석 + TODO 생성 + 우선순위/의존성 부여
- **Tool Chooser**: 어떤 툴을 어떤 파라미터로 호출할지 결정(설명서 기반)
- **Solver**: 툴 없이 해결 가능한 TODO 처리
- **Evidence/Reporter**: 실행 결과를 사용자에게 보여줄 형태로 요약/근거화

> 원칙: LLM은 무상태이므로, 매 호출마다 **역할에 맞는 최소 컨텍스트**를 편지에 포함한다.

### 3.3) 프롬프트 조립 원칙 (역할별 최소 컨텍스트)

- 고정 지침(System/Role)과 가변 지침(요약 히스토리/메모리/툴설명)을 분리한다.
- 역할별로 필요한 정보만 주입한다.
  - GM Router: system + role(router) + 사용자 요청 + 최소 상태
  - DeepAgent Planner: system + role(planner) + 요약 히스토리 + 사용자 요청
  - DeepAgent Tool-Chooser: system + role(tool_select) + todo + 툴 목록 요약
  - DeepAgent Param Builder: system + role(tool_param) + todo + 선택된 툴 상세 설명
  - DeepAgent Reporter/Evidence: system + role(report) + 실행 결과 + 핵심 근거
- ToolSpec은 단일 소스로 관리하고, **필요한 툴만** 요약해 주입한다.

### 3.4) 로그/근거 주입 규칙 (필요 시만)

- 사용자 UI에는 전체 로그를 저장/표시하되, LLM에는 기본적으로 요약 상태만 제공한다.
- 로그 주입은 규칙 기반으로 결정한다.
  - 실패/예외 발생 시
  - 사용자 질문이 “왜/근거/설명” 성격일 때
  - 재시도 판단이 필요한 오류 유형일 때
  - 승인/거부 사유 설명이 정책상 필요한 경우
- GM LangGraph의 `CheckIntent` 같은 노드에서 분기하고,
  필요 시에만 DeepAgent 보고(Evidence/Reporter)를 호출한다.

### 3.5) Orchestration Engine (LangGraph, 고정 사용)

- **GeneralManager는 LangGraph를 고정 사용**한다.
- DeepAgent는 라이브러리 내부에서 LangGraph를 사용할 수 있으나, 시스템 오케스트레이션은 GM이 담당한다.
- JobRunner는 실행 어댑터로서 DeepAgent 실행/중단/상태 수집을 수행한다.
- 노드별로 서로 다른 LLM Provider 호출은 지원하며, ProviderAdapter로 분리한다.
- 설계/구현 단순화를 우선하며, 엔진 교체 가능성은 당장 고려하지 않는다.


---

## 4) Job / Worker 동작 규칙

### 4.1 Job 단위 동시성
- 여러 Job은 WorkerPool(N개)에서 **동시에** 실행될 수 있다.
- 각 Job 내부에서는 TODO를 **순차 실행**한다. (네비 완료 후 다음 행동 같은 의존성을 보장)
- DeepAgent는 병렬 작업을 생성할 수 있으나, **ToolBox를 사용하는 툴 실행은 순차를 보장**한다.

### 4.2 Worker 상태 (전광판 표시)
- RUNNING: 실행 중
- WAITING_LOCK: 툴 락/재고 대기 (노란색 깜빡)
- WAITING_CONFIRM: 사용자 승인/선택 대기 (노란색 깜빡)
- DONE: 완료 (초록색 깜빡)
- FAILED: 실패 (빨강색 깜빡)
- CANCELED: 취소 (회색)

### 4.3 사용자 확인 인터럽트
다음 상황에서 UI 승인/선택이 필요할 수 있다.

- Tool 실행 자체가 “승인 필요” 정책인 경우(예: 네비 목적지 변경, 결제 등)
- 공구(툴)가 **잠겨있거나 재고가 없는 경우**(수량/그룹락)

사용자 선택(예시):
- **대기(wait)**: 해당 공구가 풀릴 때까지 기다렸다가 재시도
- **취소(cancel)**: 현재 Job을 종료
- **중단(stop_other)**: **충돌 중인 Job(해당 공구/그룹을 점유 중인 Job)**을 취소하고 현재 Job을 진행

---

## 5) 공구박스(ToolBox) 설계 규칙

### 5.1 툴 수량(capacity)
- NavTool: 1
- MovieTool: 1
- SongTool: 2
- WeatherTool: infinite (락 없음)

### 5.2 그룹락(모니터박스)
- MonitorBox 그룹: NavTool, MovieTool이 같은 박스에 포장됨
- MonitorBox capacity = 1
- 즉, NavTool을 누가 쓰는 동안 MovieTool도 못 쓴다. (그룹락)

### 5.3 Acquire / Release (ToolRuntimeAdapter 경유)
- DeepAgent의 툴 호출은 ToolRuntimeAdapter를 통해 ToolBox로 라우팅된다.
- 어댑터는 실행 전 `Acquire(toolKey, groupKey)`로 “대여”한다.
- 성공(acquired) 시 실행 후 반드시 Release로 반납한다.
- 실패(locked) 시:
  - 기본 정책: 사용자에게 “대기/취소/중단” 선택을 요구한다.
  - 대기를 선택하면 같은 TODO의 Acquire를 재시도한다. (순차 보장)
  - 중단(stop_other)은 충돌 Job을 JobManager가 취소한 뒤 재시도한다.
- 승인 필요(confirmPolicy) 시:
  - ToolRuntimeAdapter가 **승인 인터럽트**를 발생시키고 DeepAgent를 일시 중단한다.
  - 승인/거부 결과에 따라 실행/취소로 분기한다.

---

## 6) UI

### 6.1 UI 참고 프로젝트

- UI 베이스로 가져갈 레퍼런스(오픈소스): `https://github.com/Wanderson-Magalhaes/Modern_GUI_PyDracula_PySide6_or_PyQt6`
- 본 프로젝트의 레이아웃/컴포넌트 스타일을 참고하여, Chat View + Dashboard + Job Panel을 구성한다.

### 6.2 UI 구성 (전광판 + 작업 패널)

- 전광판(Dashboard)
  - 워커/잡을 아이콘으로 표시
  - 상태에 따라 색/깜빡임: 실행중/대기(노랑)/성공(초록)/실패(빨강)
  - 아이콘 클릭 시 Job Panel 오픈

- 작업 패널(Job Panel)
  - 해당 Job 전용 채팅/로그 화면
  - 툴 로그 실시간 표시(Log Stream)
  - 승인/대기/취소/중단 버튼 제공

---

## 7) 예시 시나리오

### 7.1 네비 실행 중 노래 실행(동시 가능)
- Job1: NavTool(모니터박스 점유) 실행
- Job2: SongTool 1개 대여 후 실행(가능)

### 7.2 네비 실행 중 영화 요청(충돌 발생)
- Job2가 MovieTool 필요
- MonitorBox가 점유되어 locked
- Job2는 사용자 선택 대기:
  - wait: 네비 끝난 뒤 MovieTool 재시도
  - cancel: Job2 종료
  - stop_other: **충돌 Job(네비, MonitorBox 점유)** 취소 후 MovieTool 실행

---

## 8) 구현 파일 안내

- 플로우차트(v3): `agent_world_flowchart_v3.md`
- 구조/상태머신: `agent_world_models_v2.md`
- 역할/세계관: `agent_world_roles_v4.md`

---

끝.
