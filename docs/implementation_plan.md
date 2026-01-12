# 구현 계획 (Draft)

이 문서는 현재 문서 구조(GM LangGraph + DeepAgent Worker + ToolRuntimeAdapter)를 기준으로 구현 순서를 정리한다.

---

## 0) 전제

- GM은 LangGraph로 입력 분기만 담당한다.
- DeepAgent는 내부 그래프/미들웨어를 사용하며 tools 호출은 ToolRuntimeAdapter 경유로 강제한다.
- ToolBox는 단일 ToolSpec/Inventory 소스이며 정책은 Adapter가 적용한다.

---

## 1) 1단계: 기본 런타임 골격

### 상세 작업 리스트
- 폴더 생성: `app/world/`, `app/world/gm/`, `app/world/worker/`
- 공통 타입 정의
  - `JobState`, `WorkerState`
  - `JobRecord`, `ToolCallRecord`
- JobManager 기본 구현
  - `create_job`, `get_job`, `list_jobs`, `cancel_job`
  - in-memory 저장소 우선
- 이벤트 버스 기본 구현
  - `publish_event`, `subscribe`
  - UI 업데이트 포맷 정의

---

## 2) 2단계: ToolRuntimeAdapter MVP

### 상세 작업 리스트
- Adapter 클래스 스켈레톤
  - `acquire`, `confirm_if_needed`, `execute_tool`, `release`
- ToolBox Inventory 연동
  - groupKey/capacity 체크
  - locked/acquired 분기
- UI 인터럽트 이벤트
  - `waiting_lock`, `waiting_confirm`
- 실행 로그 스트림
  - tool 실행 로그 수집/전달

---

## 3) 3단계: GM LangGraph 라우팅

### 상세 작업 리스트
- 라우팅 그래프 노드 작성
  - `intent_route`
  - `job_create`, `job_status`, `job_cancel`, `job_result`, `job_list`
- 입력 포맷 정의
  - START/STATUS/CANCEL/RESULT/LIST
- 응답 포맷 정의
  - `job_id`, `state`, `summary`

---

## 4) 4단계: WorkerPool + JobRunner

### 상세 작업 리스트
- WorkerPool 스케줄링 정책
  - FIFO 또는 Round-robin
- JobRunner 라이프사이클
  - start/stop
  - 상태 업데이트
- cancel 처리
  - running -> canceled 전환

---

## 5) 5단계: DeepAgent 통합

### 상세 작업 리스트
- DeepAgent 래퍼 정의
  - 입력: `plan/todo`
  - 출력: `result`, `evidence`
- tools 호출 경로 고정
  - ToolRuntimeAdapter 경유
- 미들웨어 체인 확인
  - PatchToolCalls/Summarization/TodoList/tools

---

## 6) 6단계: UI 연결 강화

### 상세 작업 리스트
- Dashboard 상태 반영
  - RUNNING/WAITING_LOCK/WAITING_CONFIRM
- Job Panel 버튼 연결
  - approve/reject, wait/cancel/stop_other
- 로그 스트림 안정화
  - UI 끊김/중복 방지

---

## 7) 테스트/검증 시나리오

### 상세 작업 리스트
- 락 충돌 시나리오 재현 스크립트
- 승인 필요 시나리오 재현 스크립트
- 동시 job 실행 시나리오 재현 스크립트
- cancel 즉시 반영 확인

---

끝.
