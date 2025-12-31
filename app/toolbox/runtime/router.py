class ToolRuntime:
    def __init__(self, adapters):
        self._adapters = adapters

    def invoke(self, tool_key: str, args):
        raise NotImplementedError("Route to adapter and invoke")
