from .base import ToolAdapter

class McpAdapter(ToolAdapter):
    def invoke(self, spec, args):
        raise NotImplementedError
