from .base import ToolAdapter

class SkillsAdapter(ToolAdapter):
    def invoke(self, spec, args):
        raise NotImplementedError
