from pyximportx.handler import handler

class __loader:
    def load_module(self, module_name):
        return handler.load_pyximportx_module(module_name)

loader = __loader()