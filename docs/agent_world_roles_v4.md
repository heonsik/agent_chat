# 에이전트 세계관(역할/클래스) 정리 문서

이 문서는 ‘가게’ 비유를 기반으로 프로그램 구성 요소의 역할, 책임, 상호작용을 개발 관점에서 정리합니다.

---

## 0) 핵심 요약

- **총괄매니저(GeneralManager, LangGraph)**는 입력을 분기하고 Job을 생성/조회/취소하며 즉시 응답한다.
- **딥에이전트(DeepAgent, Worker)**는 장시간 작업을 수행하고 툴 호출/판단/요약까지 책임진다.
- **ToolRuntimeAdapter**가 DeepAgent의 툴 호출을 **ToolBox 정책(Acquire/Release, 승인, 그룹락)**으로 감싼다.
- 모든 진행 상태는 **Dashboard/Job Panel**에서 실시간 표시되고, 승인/대기/취소/중단은 UI에서 처리한다.

---

## 1) 캐릭터/컴포넌트 역할과 책임

### 1) 딥에이전트 (DeepAgent / Worker)
**정의**: Job을 받아 장시간 작업을 수행하는 워커. 내부에서 계획/툴선택/파라미터 구성/실행/요약을 수행한다.

- 주요 책임
  - 요청을 TODO로 분해하고 순차 처리
  - 툴 호출 및 결과 요약
  - 로그/근거를 JobManager에 전달
- 정책
  - ToolBox 사용 툴은 **순차 실행**을 보장
  - 승인/락 인터럽트 시 즉시 대기

---

### 2) 고객 (Customer / User)
**정의**: 프로그램에 입력을 주고 결과를 받는 주체.

- 특징
  - 작업이 진행 중이어도 **추가 입력** 가능
  - 승인/대기/취소/중단 선택은 UI에서 수행

---

### 3) 총괄매니저 (GeneralManager / LangGraph)
**정의**: 최상위 오케스트레이터. 입력을 분기하고 Job을 생성/조회/취소한다.

- 주요 책임
  - 입력 분기: START/STATUS/CANCEL/RESULT/LIST
  - JobManager에 작업지시서 제출
  - 즉시 응답(블로킹 금지)

---

### 4) JobManager
**정의**: Job 메타/상태/로그를 저장하고 WorkerPool로 배차한다.

- 주요 책임
  - job_id 발급
  - 상태 저장: queued/running/waiting_lock/waiting_confirm/done/failed/canceled
  - 로그/진행률/결과 저장

---

### 5) WorkerPool + JobRunner
**정의**: Job을 워커에게 전달하고 실행을 모니터링하는 실행기.

- WorkerPool: 동시 실행 워커 풀 관리
- JobRunner: DeepAgent 실행/중단/상태 수집/로그 스트림

---

### 6) ToolRuntimeAdapter + ToolBox
**정의**: DeepAgent의 툴 호출을 정책으로 감싸는 실행 계층.

- ToolRuntimeAdapter
  - Acquire/Release 강제
  - confirmPolicy 및 lock 충돌 처리
  - UI 인터럽트 발생 및 재개
- ToolBox
  - capacity/groupKey/confirmPolicy의 단일 소스

---

### 7) 프로그램 UI (agent_chat / Store UI)
**정의**: Chat + Dashboard + Job Panel로 상태/로그/승인을 표시.

- Chat View: 입력/응답
- Dashboard: 워커/잡 상태 표시
- Job Panel: 작업 로그/승인 버튼

---

### 8) ProviderAdapter (선택)
**정의**: LLM Provider 입출력 정규화. 필요 시 GM/Worker 모두에 적용.

---

## 2) 핵심 정책(세계관 규칙을 코드 정책으로)

### 2.1 GM은 블로킹하지 않는다
- 긴 작업은 Job으로 제출하고 즉시 응답한다.

### 2.2 Job 내부는 순차 실행
- TODO는 순서 보장
- ToolBox가 연동된 툴 실행은 반드시 순차

### 2.3 승인/락은 UI가 결정
- 승인 필요: approve/reject
- 락 충돌: wait/cancel/stop_other

---

## 3) 예시 시나리오

### 시나리오 A: 네비 실행 중 노래 실행
1) Job1: NavTool(모니터박스 점유) 실행
2) Job2: SongTool 실행 (가능)
3) Dashboard에서 두 Job 상태 동시 표시

### 시나리오 B: 네비 실행 중 영화 요청(충돌)
1) MovieTool 필요
2) MonitorBox가 점유되어 locked
3) UI 선택: wait / cancel / stop_other

### 시나리오 C: SongTool 2개 모두 사용 중
1) SongTool 재고 없음
2) UI에서 wait/cancel 선택

---

## 4) 관련 파일

- 플로우차트(세계관 동작): `agent_world_flowchart_v3.md`
- 구조/상태머신: `agent_world_models_v2.md`
- 프로그램 설명서: `agent_world_program_spec_v4.md`

---

끝.
