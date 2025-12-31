from .base import ToolAdapter

class LocalAdapter(ToolAdapter):
    def invoke(self, spec, args):
        raise NotImplementedError
