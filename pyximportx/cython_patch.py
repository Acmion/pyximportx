import os

from pyximportx.handler import handler

from Cython.Compiler.Main import Context
from Cython.Compiler import Options

Options.annotate = True
Options.cimport_from_pyx = True

def find_pxd_file(self, qualified_name, pos=None, sys_path=True, source_file_path=None):
    # return the source file itself and let cython handle the cimports
    
    pxd = self.search_include_directories(
            qualified_name, suffix=".pxd", source_pos=pos, sys_path=sys_path, source_file_path=source_file_path)

    if pxd is None and Options.cimport_from_pyx:
        pyx_file_path = handler.resolve_module_pyx_file_path(qualified_name) 
        if os.path.exists(pyx_file_path):
            return pyx_file_path
        else:
            return None
        
    return pxd
    

Context.find_pxd_file = find_pxd_file
