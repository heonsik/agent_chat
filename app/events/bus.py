from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict, List, Type


Handler = Callable[[Any], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: DefaultDict[Type[Any], List[Handler]] = defaultdict(list)

    def subscribe(self, event_type: Type[Any], handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def emit(self, event: Any) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)
