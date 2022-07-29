from importlib.abc import MetaPathFinder
from pyximportx.handler import handler
from pyximportx.loader import loader

class __meta_path_finder(MetaPathFinder):
    def find_module(self, module_name: str, path: object):
        if path == None:
            # trying to compile a module's __init__.py file.
            # could not get this to work :(

            # let some other meta path finder deal with this
            return None
        else:
            if handler.should_module_be_handled(module_name):
                return loader

meta_path_finder = __meta_path_finder()