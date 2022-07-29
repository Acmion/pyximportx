**Pyximportx**
==========

Pyximportx is an experimental Cython compilation pipeline. It extends the functionality of `pyximport`, but with some significant improvements (see features below). This library is meant for use cases where highly iterative code development and high computational performance is preferred, for example, data science.  



Features
--------

1. Imported Cython files just work. No need for a setup configuration (e.g. `setup.py`). No need for a separate build step.
2. No need for `.pxd` files (although if provided, then they are respected).
3. Automatic `cimport` (note: see limitations), which are required for better performance.
4. Automatically handled nested Cython dependencies.
5. Standard `.py` files are used, which means better IDE support.
6. Files are compiled into the current working directory (and not to the user home directory). Thus, the files are easier to access.
7. Compiled files are cached and are thus not compiled needlessly. 



Usage
--------

1. Clone.
2. Create virtual env:
    ```
    python -m venv .venv
    ```
3. Activate virtual env (this is for Windows, probably similar for Linux):
    ```
    . .venv/Scripts/activate
    ```
4. Install dependencies:
    ```
    pip install -r requirements.txt 
    ```
5. Install pyximportx as package (so that it can be imported):
    ```
    pip install -e pyximportx
    ```
6. Write Cython code in pure Python mode and in `.py` files. The first line in all of these files should be:
    ```python
    # pyximportx
    ```
7. Write an entrypoint file (this file is not compiled with pyximportx). Import pyximportx first (this will initialize everything) and then start importing your Cython files:
    ```python
    import pyximportx

    import my.pyximportx.cython.module
    ```
8. For an example, view the `example` directory. The code can be executed with:
    ```
    python example
    ``` 
    Try also what happens when you change some functions slightly.

9. You can delete the generated files by deleting the `.pyximportx` directory or by running:
    ```python
    import pyximportx.handler as handler

    # deletes all generated files
    handler.delete_all_generated_files()

    # deletes all inplace generated files
    handler.delete_inplace_generated_files()
    ```



Limitations
-----------

- All `.py` files that should be handled by Pyximportx must begin with this:
    ```
    # pyximportx
    ```
    Other files will not be handled. 

- Only files in the current working directory are handled (excluding a virtual environment).

- Only Cython's pure Python mode is supported.
    - Not everything can be correctly typed in the pure Python mode. For example, see: https://github.com/cython/cython/issues/4907
    - You can still use the standard cdef syntax. It is just not handled by Pyximportx.

- The automatic `cimport` feature is only able to resolve the following import statements:
    ```python
    import module.sub_module as sub_module
    from module.sub_module import a, b, c
    ```

    The following is not supported:
    
    ```python
    import module.sub_module
    ```

    This is caused by a limitation in Cython.

- Only top level imports are supported.
- Changing a file that many modules depend on means that all the depending modules must also be recompiled.
- Circular imports are not supported.
- Pyximportx generates files next to your source files.
    - Could be patched, however, it is quite convenient to just exlcude the files from one's IDE.
- Python `__init__.py` files are not supported (seems to be a limitation with Cython).
- The code could be made more efficient, however, compilation is still the biggest bottleneck.
- Pyximportx does not support configuration (file names etc. are hard coded into the source).
- Pyximportx changes the global settings of the Cython compiler (could be fixed relatively easily).
- The modification time of files are used to determine whether they have changed or not. This is not entirely accurate.
- No parallel compilation.
- Everything is based on string operations. No code is parsed into an AST, which means that Pyximport is not as efficient as possible (although parsing into an AST would also incur a cost). 
- Only modules where the `.` (dot) can be replaced with a `/` (slash) to determine its source file are supported. 
    - A file named `module/sub_module.py` (imported as `module.sub_module`) is supported.
    - A file named `module/sub$module.py` is not supported.
    - The source file path of a module is always determined like this:
        ```python
        source_file_path = base_path + "module.sub_module".replace(".", "/") + ".py"

        # => 
        # source_file_path = "/path/to/cwd/module/sub_module.py"
        ```
     
- Maybe something more.





Architecture
------------

1. Importing Pyximportx installs the pipeline.
2. The meta path finder from `pyximportx/meta_path_finder.py` is inserted into `sys.meta_path`.
    - This meta path finder determines whether modules should be handled by Pyximportx or not.
3. Pyximportx modules are then registered with the loader from `pyximportx/loader.py`.
4. Modules are handled by `pyximportx/handler.py:load_pyximportx_module`.
5. All pyximportx modules will first be "compiled" into a corresponding `.pyx` file. The automatically added `cimport` statements go there.
6. Finally, the generated `.pyx` files get compiled and the modules loaded.

The code is fairly simple.

Additional Information
-----------
See this discussion for some context: https://github.com/cython/cython/issues/4892 