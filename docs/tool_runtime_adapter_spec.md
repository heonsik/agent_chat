# ToolRuntimeAdapter 인터페이스 상세 설정

이 문서는 DeepAgent가 호출하는 tools를 ToolBox 정책으로 감싸기 위한 ToolRuntimeAdapter의 계약을 정의한다.

---

## 1) 목적과 범위

- 목적: ToolBox 재고/그룹락/승인 정책을 강제하면서 tool 실행을 안전하게 중계
- 범위: Acquire/Confirm/Execute/Release 수명주기, 이벤트/상태, 오류 처리

---

## 2) 핵심 책임

- ToolBox 기반 인벤토리 검사 및 대여/반납
- 승인 필요 시 UI 인터럽트 발생 및 재개
- 락 충돌 시 대기/취소/중단 정책 처리
- 로그 스트림/상태 업데이트 제공

---

## 3) 입력/출력 계약

### 3.1 입력

- `job_id`: 작업 식별자
- `todo_id`: 현재 todo 식별자
- `tool_key`: ToolSpec 식별자
- `group_key`: 그룹락 키(없으면 null)
- `params`: tool 호출 파라미터
- `confirm_policy`: always/auto/never (ToolSpec 기반)

### 3.2 출력

- `state`: running | waiting_lock | waiting_confirm | done | failed | canceled
- `result`: tool 실행 결과(성공 시)
- `error`: 실패 요약(실패 시)
- `evidence`: 사용자용 요약/근거(선택)

---

## 4) 상태/이벤트

### 4.1 상태 전이(요약)

- `running -> waiting_lock -> running`
- `running -> waiting_confirm -> running`
- `running -> done | failed | canceled`

### 4.2 이벤트

- `waiting_lock`: 재고 부족 또는 그룹락 충돌
- `waiting_confirm`: 승인 필요
- `log_stream`: 실시간 로그 스트림
- `state_update`: 상태 변경 알림

---

## 5) 실행 수명주기

1. `Acquire(tool_key, group_key)`
2. `ConfirmIfNeeded(confirm_policy)`
3. `ExecuteTool(tool_key, params)`
4. `Release(handle)`

실패 시에도 `Release`는 반드시 시도한다.

---

## 6) 정책 처리

- **락 충돌**: UI에 wait/cancel/stop_other 선택 요청
- **승인 필요**: approve/reject 요청 후 분기
- **중단(stop_other)**: 충돌 Job 취소 후 재시도

---

## 7) 오류 처리

- Acquire 실패: `waiting_lock` 이벤트로 전환
- Tool 실행 실패: `failed`로 종료하고 error 기록
- 승인 거부: `canceled`로 종료

---

## 8) 동시성/순차성

- Job 내부 tool 호출은 **순차 실행**을 보장
- ToolBox를 사용하는 호출은 **Acquire-Execute-Release** 원자 흐름으로 처리

---

## 9) 로깅 규칙

- 모든 tool 실행은 `log_stream`을 통해 UI로 전달
- 오류 시 `error`와 함께 핵심 로그 요약 제공

---

끝.
