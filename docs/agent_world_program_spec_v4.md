# 에이전트 프로그램 설명서 (세계관 기반)

이 문서는 ‘가게 세계관’(통역가/총괄매니저/서버/공구박스/전광판) 기반으로 프로그램이 어떻게 동작해야 하는지 **구현 관점**에서 설명합니다.

---

## 1) 용어 매핑 (세계관 -> 코드)

- **고객(Customer)**: 사용자 입력/출력의 주체
- **프로그램(agent_chat / UI)**: Chat View + 전광판(Dashboard) + Job Panel
- **총괄매니저(GeneralManager / Main Thread)**: 입력을 받고 계획을 만들고 Job을 제출
- **통역가(Interpreter / LLM)**: 편지(문자열) 기반의 플래너/요약가/툴선택가/리포터
- **프로바이더(ProviderAdapter)**: LLM별 I/O 포맷을 통일하는 어댑터
- **서버들(WorkerPool + JobRunner)**: Job을 받아 TODO를 순차 실행
- **공구박스(ToolBox)**: 툴 인벤토리(수량, 그룹락, 대여/반납)
- **전광판(Dashboard)**: 워커/잡 상태를 상시 표시하는 UI 컴포넌트(색/깜빡임)
- **전광판 상태관리자(DashboardBoard)**: 전광판(UI)의 상태를 이벤트로 갱신하는 백엔드 컴포넌트

---

## 2) 실행 개요 (Top-level)

1. 고객이 채팅으로 요청한다.
2. 총괄매니저는 컨텍스트를 조립하고 통역가(LLM Planner)에게 “편지”를 보낸다.
3. 통역가가 (a) 바로 답변 가능한지 판단하거나 (b) TODO 리스트를 만들어 준다.
4. TODO가 있으면 총괄매니저는 JobManager에 작업지시서를 제출하고 즉시 입력대기로 복귀한다.
5. 서버(워커)는 Job을 가져가 TODO를 끝까지 순차 실행한다.
6. 툴 실행 중 로그/상태는 UI에 스트리밍되고, 승인/충돌/락 대기는 Job Panel에서 처리한다.

---

## 3) LLM 호출 지점 (성능 최우선)

성능 우선(정확도/유연성 우선)일 때 권장 호출 포인트:

- **Planner**: 요청 해석 + TODO 생성 + 우선순위/의존성 부여
- **Tool Chooser**: 어떤 툴을 어떤 파라미터로 호출할지 결정(설명서 기반)
- **Solver**: 툴 없이 해결 가능한 TODO 처리
- **Evidence/Reporter**: 실행 결과를 사용자에게 보여줄 형태로 요약/근거화

> 원칙: LLM은 무상태이므로, 매 호출마다 **히스토리 요약 + 중요 메모리 + 툴설명서**를 편지에 포함한다.


### 3.1) Orchestration Engine (LangGraph, 고정 사용)

- 실행 그래프는 LangGraph를 고정 사용한다.
- JobRunner 내부 플로우(Plan → ToolSelect → Acquire → Confirm → Exec)는 LangGraph 노드/엣지로 모델링한다.
- 노드별로 서로 다른 LLM Provider 호출은 지원하며, ProviderAdapter로 분리한다.
- 설계/구현 단순화를 우선하며, 엔진 교체 가능성은 당장 고려하지 않는다.


---

## 4) Job / Worker 동작 규칙

### 4.1 Job 단위 동시성
- 여러 Job은 WorkerPool(N개)에서 **동시에** 실행될 수 있다.
- 각 Job 내부에서는 TODO를 **순차 실행**한다. (네비 완료 후 다음 행동 같은 의존성을 보장)

### 4.2 Worker 상태 (전광판 표시)
- RUNNING: 실행 중
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

### 5.3 Acquire / Release
- Worker는 실행 전 `Acquire(toolKey, groupKey)`로 “대여”한다.
- 성공(acquired) 시 실행 후 반드시 Release로 반납한다.
- 실패(locked) 시:
  - 기본 정책: 사용자에게 “대기/취소/중단” 선택을 요구한다.
  - 대기를 선택하면 같은 TODO의 Acquire를 재시도한다. (순차 보장)

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
