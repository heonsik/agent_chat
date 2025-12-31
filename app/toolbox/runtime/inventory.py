class Inventory:
    def acquire(self, tool_key: str):
        raise NotImplementedError("Acquire tool")

    def release(self, handle) -> None:
        raise NotImplementedError("Release tool")
