from __future__ import annotations

from typing import Dict


def set_worker_status(ui, states: Dict[str, str]) -> None:
    ui.dashboard_list.clear()
    for worker_id, state in states.items():
        ui.dashboard_list.addItem(f"{worker_id}: {state}")


def set_confirm_state(ui, state: str) -> None:
    mapping = {"idle": 0, "lock": 1, "approve": 2}
    ui.confirm_stack.setCurrentIndex(mapping.get(state, 0))
