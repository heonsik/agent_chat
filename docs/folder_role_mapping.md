# 폴더 역할 매핑

현재 `app/world/` 아래 폴더들을 구현 계획의 컴포넌트에 매핑한다. 기존 구조를 유지한다.

---

## 매핑

- `app/world/general_manager/` -> GeneralManager (GM LangGraph 라우팅)
- `app/world/job_manager/` -> JobManager (job 상태/저장)
- `app/world/worker_pool/` -> WorkerPool (워커 스케줄링)
- `app/world/job_runner/` -> JobRunner (DeepAgent 실행 어댑터)
- `app/world/adapter/` -> ToolRuntimeAdapter (ToolBox 정책 중계)
- `app/world/lock_manager/` -> ToolBox/Inventory 보조(락/재고 보조 로직)
- `app/world/dashboard/` -> DashboardBoard (상태 이벤트/표시)

---

## 정리 방침

- 기존 폴더는 삭제/이동하지 않는다.
- 역할 중복은 문서로만 명확히 한다.

---

끝.
