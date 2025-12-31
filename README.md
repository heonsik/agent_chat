# agent_chat

agent_chat is a UI-first orchestration prototype with a world-model workflow
(GeneralManager, JobManager, WorkerPool, JobRunner, Toolbox, Dashboard).

## Quick Start

1) Create a venv and install deps:

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

2) Run the app:

```powershell
.\.venv\Scripts\python main.py
```

## Structure

```
app/                 Project code (world, llm, toolbox, ui)
app/ui_vendor/       PyDracula vendor assets (modules, widgets, themes, images)
docs/                World docs (roles/spec/flowchart/models)
tests/               Placeholder for tests
scripts/             Placeholder for scripts
main.py              App entry
```

## Toolbox Registry

Tool specs and adapters live under:

```
app/toolbox/specs/
app/toolbox/runtime/
app/toolbox/adapters/
app/toolbox/tools_local/
```

