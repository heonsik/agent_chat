from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _append(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")


def append_ledger(line: str) -> None:
    _append(BASE_DIR / "ledger" / "ledger.log", line)


def append_evidence(line: str) -> None:
    _append(BASE_DIR / "evidence" / "evidence.log", line)


def append_log(line: str) -> None:
    _append(BASE_DIR / "logs" / "tool.log", line)
