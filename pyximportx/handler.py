import imp

import os
import pyximport.pyxbuild
import glob
import datetime
import re
import shutil

from pyximportx.dependency import dependency

class __handler():

    # general

    def resolve_root_directory_path(self):
        return os.getcwd() + "/"

    def resolve_venv_directory_path(self):
        return os.environ['VIRTUAL_ENV'] + "/"

    def resolve_pyximportx_directory_path(self):
        return self.resolve_root_directory_path() + "/.pyximportx/"

    def resolve_pyximportx_out_directory_path(self):
        return self.resolve_pyximportx_directory_path() + "/.out/"


    # delete generated files

    def delete_all_generated_files(self):
        self.delete_inplace_generated_files()
        self.delete_pyximport_directory_generated_files()

    def delete_inplace_generated_files(self):
        dep_files = glob.glob(self.resolve_root_directory_path() + "**/*.py.dep", recursive = True)

        for df in dep_files:
            # drop .dep from file and add x => .py.dep = .pyx 
            pyx_file = df[0:len(df) - 4] + "x"

            os.unlink(df)
            os.unlink(pyx_file)

    def delete_pyximport_directory_generated_files(self):
        shutil.rmtree(self.resolve_pyximportx_directory_path(), True)


    # module file resolution

    def resolve_module_file_path(self, module_name: str):
        root = self.resolve_root_directory_path()

        module_relative = module_name.replace(".", "/") + ".py"

        return root + module_relative

    def resolve_module_pyx_file_path(self, module_name: str):
        module_file_path = self.resolve_module_file_path(module_name)

        return module_file_path + "x"

    def resolve_module_extension_file_path(self, module_name: str):
        root_dir_path = self.resolve_root_directory_path()
        module_file_path = self.resolve_module_file_path(module_name)
        
        module_file_path_without_root_dir = module_file_path.replace(root_dir_path, "", 1)

        return self.resolve_pyximportx_out_directory_path() + module_file_path_without_root_dir + ".ext"

    def resolve_module_annotation_file_path(self, module_name: str):
        return self.resolve_module_extension_file_path(module_name) + ".html"

    def resolve_module_dependency_file_path(self, module_name: str):
        return self.resolve_module_file_path(module_name) + ".dep"

    def resolve_cythonized_module_annotation_file_path(self, module_name: str):
        """
        Cython creates html annotation files in some directory. This method resolves the path to an annotation file.

        Cython html annotation path example: "D:/Acmion/pyximportx/.pyximportx/temp.win-amd64-cpython-310/Release/Acmion/pyximportx/system/types.html"

        The portion "temp.win-amd64-cpython-310/Release" is difficult (or annoying) to determine upfront. This method resolves this with a glob.
        """

        pyximport_dir_path = self.resolve_pyximportx_directory_path()
        module_file_path = self.resolve_module_file_path(module_name)

        module_dir_path = os.path.dirname(module_file_path)
        module_file_name = module_file_path.replace(module_dir_path, "")

        # remove drive (e.g. C:/) from path on windows
        drive, module_dir_path = os.path.splitdrive(module_dir_path)

        return glob.glob(pyximport_dir_path + "temp*/**/" + module_dir_path + "/" + module_file_name.replace(".py", ".html"), recursive = True)[0]

    def get_module_modified_time(self, module_name: str):
        return os.path.getmtime(self.resolve_module_file_path(module_name))


    # should pyximportx handle a module

    def is_module_local(self, module_name: str):
        norm_root_dir_path = os.path.normpath(self.resolve_root_directory_path())
        norm_venv_dir_path = os.path.normpath(self.resolve_venv_directory_path())
        norm_module_file_path = os.path.normpath(self.resolve_module_file_path(module_name))

        is_local = norm_module_file_path.startswith(norm_root_dir_path)
        is_venv = norm_module_file_path.startswith(norm_venv_dir_path)

        return is_local and not is_venv

    def is_module_pyximportx(self, module_name: str):
        module_file_path = self.resolve_module_file_path(module_name)
        
        if not os.path.exists(module_file_path):
            return False

        first_line = ""
        
        with open(module_file_path) as f:
            first_line = f.readline().strip()

        is_cy_file = first_line.startswith("# pyximportx")

        return is_cy_file


    def should_module_be_handled(self, module_name: str):
        return self.is_module_local(module_name) and self.is_module_pyximportx(module_name)


    # compilation

    def load_pyximportx_module(self, module_name: str):
        if self.should_module_be_reloaded(module_name):
            extension_file_path = self.build_pyximportx_module(module_name)
            return imp.load_dynamic(module_name, extension_file_path)

        else:
            extension_file_path = self.resolve_module_extension_file_path(module_name)
            return imp.load_dynamic(module_name, extension_file_path)

    def build_pyximportx_module(self, module_name: str):
        """
            This method does the following:
            1. Compiles a cython source file and all dependencies.
            2. Moves the compiled extension and annotations to the correct directory.
            3. Returns the file path to the built extension.
        """
        module_file_path = self.resolve_module_file_path(module_name)
        module_pyx_file_path = self.resolve_module_pyx_file_path(module_name)
        module_dep_file_path = self.resolve_module_dependency_file_path(module_name)

        pyximportx_dependencies = self.resolve_pyximportx_dependencies_from_module_file(module_name)
            
        for dep in pyximportx_dependencies:
            if self.should_module_be_reloaded(dep.module_name):
                self.build_pyximportx_module(dep.module_name)
                dep.last_modified = self.get_module_modified_time(dep.module_name)

        self.create_module_pyx_file(module_name, pyximportx_dependencies)
        self.create_module_dependency_file(module_name, pyximportx_dependencies)

        module_ext_file_path = self.resolve_module_extension_file_path(module_name)
        module_annotation_file_path = self.resolve_module_annotation_file_path(module_name)

        cythonized_extension_file_path = pyximport.pyxbuild.pyx_to_dll(module_pyx_file_path, force_rebuild = 1, 
                                                            build_in_temp = True, 
                                                            pyxbuild_dir = self.resolve_pyximportx_directory_path(),
                                                            setup_args = {},
                                                            reload_support = True,
                                                            inplace = False)

        try:
            os.renames(cythonized_extension_file_path, module_ext_file_path)
        except:
            # could not rename bc extension is in use
            # solution: move prev file and then rename

            date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
            os.rename(module_ext_file_path, module_ext_file_path + ".v" + date_str)
            os.renames(cythonized_extension_file_path, module_ext_file_path)

        if os.path.exists(module_annotation_file_path):
            os.unlink(module_annotation_file_path)
        
        os.renames(self.resolve_cythonized_module_annotation_file_path(module_name), module_annotation_file_path)

        return module_ext_file_path

    def resolve_pyximportx_dependencies_from_module_file(self, module_name: str):
        module_file_path = self.resolve_module_file_path(module_name)

        pyximportx_dependencies: list[dependency] = []
        with open(module_file_path) as module_file:
            lines = module_file.readlines()

            for line in lines:
                s0 = re.search("^import (.*) as (.*)", line)
                s1 = re.search("^from (.*) import (.*)", line)
                
                if s0 != None:
                    if self.is_module_pyximportx(s0.group(1)):
                        pyximportx_dependencies.append(dependency(s0.group(1), s0.group(2), True, self.get_module_modified_time(s0.group(1))))
                
                if s1 != None:
                    if self.is_module_pyximportx(s1.group(1)):
                        pyximportx_dependencies.append(dependency(s1.group(1), s1.group(2), False, self.get_module_modified_time(s1.group(1))))

        return pyximportx_dependencies

    def resolve_pyximportx_dependencies_from_dependency_file(self, module_name: str):
        module_dependency_file_path = self.resolve_module_dependency_file_path(module_name)

        pyximportx_dependencies: list[dependency] = []
        with open(module_dependency_file_path) as dep_file:
            lines = dep_file.readlines()

            # drop header
            for line in lines[1:]:
                pyximportx_dependencies.append(dependency.instantiate_from_string(line))

        return pyximportx_dependencies


    def should_module_be_reloaded(self, module_name: str):
        """
        Determines whether a module should be reloaded. 
        First the module source and extension file are compared.
        Then first level dependencies are checked.
        Finally, nested dependencies are checked.
        """
        module_file_path = self.resolve_module_file_path(module_name)
        module_extension_file_path = self.resolve_module_extension_file_path(module_name)

        if os.path.exists(module_extension_file_path):
            module_modified = os.path.getmtime(module_file_path)
            module_extension_modified = os.path.getmtime(module_extension_file_path)

            if module_modified > module_extension_modified:
                return True
            else:
                module_dep_file_path = self.resolve_module_dependency_file_path(module_name)

                if os.path.exists(module_dep_file_path):
                    pyximportx_dependencies = self.resolve_pyximportx_dependencies_from_dependency_file(module_name)

                    # this checks only first level dependencies, but is faster
                    for dep in pyximportx_dependencies:
                        if self.get_module_modified_time(dep.module_name) > dep.last_modified:
                            return True

                    # this checks for nested dependencies
                    for dep in pyximportx_dependencies:
                        if self.should_module_be_reloaded(dep.module_name):
                            return True

                    # nothing needs to be reloaded
                    return False
                
                else:
                    # no dep file, which means that module must be reloaded
                    return True
        else:
            return True

    def create_module_dependency_file(self, module_name: str, pyximportx_dependencies: list[dependency]):
        """
        This method writes module dependencies into a .py.dep file.

        """
        module_dep_file_path = self.resolve_module_dependency_file_path(module_name)

        with open(module_dep_file_path, "w") as dep_file:
            dep_file.write(dependency.generate_header_string() + "\n")

            for dep in pyximportx_dependencies:
                dep_file.write(dep.generate_string() + "\n")

    def create_module_pyx_file(self, module_name: str, pyximportx_dependencies: list[dependency]):
        """
        This method copies the source code from a .py file to a .pyx file.
        This code generates cimports as well as.
        The pyx file is needed for cimport_from_pyx (although that could also be patched...)
        """
        module_file_path = self.resolve_module_file_path(module_name)
        module_pyx_file_path = self.resolve_module_pyx_file_path(module_name)

        cimports: list[str] = []

        for dep in pyximportx_dependencies:
            cimports.append(dep.generate_cimport())

        source_code = ""
        source_code_cimports = "\n".join(cimports)

        with open(module_file_path) as module_file:
            source_code = f"# pyximportx\n{source_code_cimports}\n{module_file.read()}"

        with open(module_pyx_file_path, "w") as module_pyx_file:
            module_pyx_file.write(source_code)


handler = __handler()